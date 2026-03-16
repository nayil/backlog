"""Entry point for `python -m backlog`."""
import sys
from pathlib import Path

_VERSION = "1.1.0"

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def main() -> None:
    if "--version" in sys.argv:
        print(f"backlog {_VERSION}")
        sys.exit(0)

    from app import BacklogApp
    BacklogApp().run()


if __name__ == "__main__":
    main()
