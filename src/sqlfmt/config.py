import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from sqlfmt.exception import SqlfmtConfigError

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


Config = Dict[str, Union[bool, int]]


def load_config_file(files: List[str]) -> Config:
    """
    files is a list of resolved, absolute paths (like the ones passed from the
    Click CLI). This finds a pyproject.toml file in the common parent directory
    of files (or in the common parent's parents).
    """
    config_path = _find_config_file(files)
    config = _load_config_from_path(config_path)
    return config


def _find_config_file(files: List[str]) -> Optional[Path]:
    assert files, "Must provide a list of paths"

    common_parents: Set[Path] = set()
    for p in [Path(f) for f in files]:
        parents = set(p.parents)
        if p.is_dir():
            parents.add(p)
        if not common_parents:
            common_parents = parents
        else:
            common_parents &= parents

    # the root directory is the lowest (i.e. most specific)
    # common parent among all of the files passed to sqlfmt
    root_dir = max(common_parents, key=lambda p: p.parts)

    search_paths = [root_dir, *root_dir.parents]

    for f in [dir / "pyproject.toml" for dir in search_paths]:
        if f.exists():
            return f
    else:
        return None


def _load_config_from_path(config_path: Optional[Path]) -> Config:

    if not config_path or not config_path.is_file():
        return {}
    else:
        try:
            with open(config_path, "rb") as f:
                pyproject_dict = tomllib.load(f)
        except OSError as e:
            # should only reach here with a race condition
            raise SqlfmtConfigError(
                f"Error opening pyproject.toml config file at {config_path}. {e}"
            )
        except tomllib.TOMLDecodeError as e:
            raise SqlfmtConfigError(
                f"Error decoding pyproject.toml config file at {config_path}. "
                f"Check for invalid TOML. {e}"
            )
        config: Config = pyproject_dict.get("tool", {}).get("sqlfmt", {})
        return config
