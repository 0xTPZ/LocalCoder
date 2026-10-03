"""Persistência JSON atômica e validada."""

from .atomic_json import AtomicJsonStore
from .jsonl import JsonlCorruptionError, JsonlReadReport, append_jsonl, append_jsonl_record, read_jsonl
from .locking import FileLock, LockConflictError, LockInfo, LockOwnershipError

__all__ = [
    "AtomicJsonStore",
    "FileLock",
    "JsonlCorruptionError",
    "JsonlReadReport",
    "LockConflictError",
    "LockInfo",
    "LockOwnershipError",
    "append_jsonl",
    "append_jsonl_record",
    "read_jsonl",
]
