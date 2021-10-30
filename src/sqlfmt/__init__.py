import sys
from pathlib import Path

if sys.version_info < (3, 8):
    from importlib_metadata import version
else:
    from importlib.metadata import version


__version__ = version("sqlfmt")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
