"""PyInstaller entry point.

PyInstaller executes the target file as a top-level script, so the package's
``__main__.py`` (which uses relative imports) fails with
"attempted relative import with no known parent package" when used directly.
This wrapper imports the package absolutely and delegates to its main().
"""
import sys

from spass_csv_converter.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
