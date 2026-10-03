"""Medições locais portáteis; indisponibilidade explícita vira NOT_TESTED."""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    ram_total_gib: float | None
    ram_available_gib: float | None
    cpu_percent: float | None = None
    gpu_percent: float | None = None
    vram_used_gib: float | None = None

    def to_document(self, prefix: str) -> dict[str, Any]:
        return {
            f"{prefix}_ram_total_gib": self.ram_total_gib,
            f"{prefix}_ram_available_gib": self.ram_available_gib,
            f"{prefix}_cpu_percent": self.cpu_percent if self.cpu_percent is not None else "NOT_TESTED",
            f"{prefix}_gpu_percent": self.gpu_percent if self.gpu_percent is not None else "NOT_TESTED",
            f"{prefix}_vram_used_gib": self.vram_used_gib if self.vram_used_gib is not None else "NOT_TESTED",
        }


def capture_resources() -> ResourceSnapshot:
    if os.name != "nt":
        return ResourceSnapshot(None, None)
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return ResourceSnapshot(None, None)
    gib = float(1024**3)
    return ResourceSnapshot(status.ullTotalPhys / gib, status.ullAvailPhys / gib)
