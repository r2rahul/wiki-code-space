"""Support ``python -m wiki_engine`` as a CLI entry point."""

from __future__ import annotations

from wiki_engine.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
