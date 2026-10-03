"""Identificadores estáveis, independentes de nomes humanos."""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5


LOCALCODER_NAMESPACE = uuid5(NAMESPACE_URL, "https://localcoder.dev/identity/v1")


def stable_id(kind: str, *parts: str) -> str:
    if not kind.strip() or any(not part.strip() for part in parts):
        raise ValueError("stable IDs require non-empty kind and parts")
    material = "\x1f".join((kind, *parts))
    return str(uuid5(LOCALCODER_NAMESPACE, material))
