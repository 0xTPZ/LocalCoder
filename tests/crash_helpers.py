"""Helpers de subprocesso usados exclusivamente pelo Crash Lab."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def project_document(status: str = "ACTIVE") -> dict[str, object]:
    return {
        "schema_version": 1,
        "project_id": "crash-project",
        "root_path": "E:\\crash-project",
        "roadmap_id": None,
        "created_at": "2026-10-03T12:00:00.000Z",
        "status": status,
        "metadata": {},
    }


def atomic_crash(path: Path) -> None:
    from localcoder.persistence import AtomicJsonStore
    from localcoder.schemas import SchemaRegistry

    store = AtomicJsonStore(path, "project", SchemaRegistry())
    store.save(project_document("PAUSED"), before_replace=lambda _: os._exit(71))


def hold_lock(path: Path) -> None:
    from localcoder.persistence import FileLock

    lock = FileLock(path, "crash-lab-lock")
    info = lock.acquire()
    print(info.lock_id, flush=True)
    time.sleep(60)


def die_before_write() -> None:
    os._exit(72)


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "atomic-crash":
        atomic_crash(Path(sys.argv[2]))
    elif command == "hold-lock":
        hold_lock(Path(sys.argv[2]))
    elif command == "die-before-write":
        die_before_write()
    else:
        raise SystemExit(f"unknown crash helper command: {command}")
