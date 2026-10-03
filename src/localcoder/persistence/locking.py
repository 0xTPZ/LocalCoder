"""Lock de arquivo conservador para estado operacional local."""

from __future__ import annotations

import json
import os
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ..state.redaction import redact
from ..state.time import format_utc, parse_utc, utc_now


class LockConflictError(RuntimeError):
    """Outro processo/instância possui o lock."""

    def __init__(self, path: Path, info: "LockInfo | None") -> None:
        self.path = path
        self.info = info
        state = "unknown owner" if info is None else f"owner pid={info.pid} lock_id={info.lock_id}"
        super().__init__(f"lock already held: {path} ({state})")


class LockOwnershipError(RuntimeError):
    """A instância que tentou liberar não é dona do lock."""


@dataclass(frozen=True, slots=True)
class LockInfo:
    lock_id: str
    pid: int
    host: str
    acquired_at: object
    resource: str

    def to_document(self) -> dict[str, object]:
        return {
            "lock_id": self.lock_id,
            "pid": self.pid,
            "host": self.host,
            "acquired_at": format_utc(self.acquired_at),
            "resource": self.resource,
        }

    @classmethod
    def from_document(cls, document: dict[str, object]) -> "LockInfo":
        return cls(
            lock_id=str(document["lock_id"]),
            pid=int(document["pid"]),
            host=str(document["host"]),
            acquired_at=parse_utc(str(document["acquired_at"])),
            resource=str(document["resource"]),
        )


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        # os.kill(pid, 0) is not a reliable liveness probe on Windows: terminated process
        # handles can still make that call appear successful. Query the process exit code.
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


class FileLock:
    """Criação exclusiva de um arquivo de metadados.

    Locks obsoletos nunca são removidos automaticamente. A remoção exige um lock_id esperado e
    confirmação de que o PID registrado não está vivo, evitando apagar outro processo após PID
    reuse ou uma falha de leitura.
    """

    def __init__(self, path: Path, resource: str | None = None) -> None:
        self.path = Path(path)
        self.resource = resource or str(self.path)
        self._info: LockInfo | None = None

    @property
    def info(self) -> LockInfo | None:
        return self._info

    def acquire(self) -> LockInfo:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        info = LockInfo(str(uuid4()), os.getpid(), socket.gethostname(), utc_now(), self.resource)
        payload = json.dumps(redact(info.to_document()), ensure_ascii=False, sort_keys=True).encode("utf-8")
        try:
            descriptor = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY, 0o600)
        except FileExistsError as exc:
            raise LockConflictError(self.path, self.inspect(self.path)) from exc
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.write(b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        self._info = info
        return info

    def release(self) -> None:
        if self._info is None:
            return
        current = self.inspect(self.path)
        if current is None or current.lock_id != self._info.lock_id:
            raise LockOwnershipError(f"lock ownership changed: {self.path}")
        self.path.unlink(missing_ok=True)
        self._info = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.release()

    @staticmethod
    def inspect(path: Path) -> LockInfo | None:
        try:
            document = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                return None
            return LockInfo.from_document(document)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def is_stale(info: LockInfo | None) -> bool:
        return info is not None and not process_is_alive(info.pid)

    @staticmethod
    def release_stale(path: Path, expected_lock_id: str) -> LockInfo:
        path = Path(path)
        info = FileLock.inspect(path)
        if info is None:
            raise LockOwnershipError(f"lock metadata is unreadable: {path}")
        if info.lock_id != expected_lock_id:
            raise LockOwnershipError(f"lock id mismatch: {path}")
        if process_is_alive(info.pid):
            raise LockConflictError(path, info)
        path.unlink(missing_ok=True)
        return info
