"""Entrada mínima para confirmar que a fundação está instalada."""

from . import __version__


def main() -> int:
    print(f"LocalCoder {__version__} — foundation only")
    print("Agent loop, model execution and resource heuristics: NOT IMPLEMENTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
