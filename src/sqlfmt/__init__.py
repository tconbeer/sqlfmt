from importlib.metadata import version
from pathlib import Path

__version__ = version("sqlfmt")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
