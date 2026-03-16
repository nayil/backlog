"""Entry point for `python -m backlog`."""
import sys

from . import __version__

_VERSION = __version__


def main() -> None:
    if "--version" in sys.argv:
        print(f"backlog {_VERSION}")
        sys.exit(0)

    from .app import BacklogApp
    BacklogApp().run()


if __name__ == "__main__":
    main()
