import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from sqlfmt.exception import SqlfmtConfigError
from sqlfmt.mode import Mode
from sqlfmt.report import STDIN_PATH

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


Config = Dict[str, Union[bool, int, List[str], str, Path]]


def load_config_file(files: List[Path], config_path: Optional[Path]) -> Config:
    """
    files is a list of resolved, absolute paths (like the ones passed from the
    Click CLI). This finds a pyproject.toml file in the common parent directory
    of files (or in the common parent's parents).

    If config_path is provided, searching for a config via files will be skipped
    entirely.
    """
    if config_path is None:
        common_parents = _get_common_parents(files)
        config_path = _find_config_file(common_parents)

    config = _load_config_from_path(config_path)
    return config


def _get_common_parents(files: List[Path]) -> List[Path]:
    """
    For a list of absolute paths, returns a Set of paths for all
    of the common parents of files
    """
    assert files, "Must provide a list of paths"
    common_parents: Set[Path] = set()
    for p in files:
        if p == STDIN_PATH:
            break
        else:
            assert p.is_absolute()
            parents = set(p.parents)
            if p.is_dir():
                parents.add(p)
            if not common_parents:
                common_parents = parents
            else:
                common_parents &= parents

    # the root directory is the lowest (i.e. most specific)
    # common parent among all of the files passed to sqlfmt
    try:
        root_dir = max(common_parents, key=lambda p: p.parts)
    except ValueError:
        # if there are no common parents (e.g., stdin), just use the cwd
        root_dir = Path.cwd()
    search_paths = [root_dir, *root_dir.parents]
    return search_paths


def _find_config_file(search_paths: List[Path]) -> Optional[Path]:
    """
    Given an ordered list of directories, returns the path to a
    pyproject.toml file in the lowest (most specific) directory

    Returns None if no file exists
    """
    for f in [p / "pyproject.toml" for p in search_paths]:
        if f.exists():
            return f
    else:
        return None


def _load_config_from_path(config_path: Optional[Path]) -> Config:
    """
    Loads a toml file located at config path. Returns the contents
    under the [tool.sqlfmt] section as a dict.
    """

    if not config_path:
        return {}
    else:
        try:
            with open(config_path, "rb") as f:
                pyproject_dict = tomllib.load(f)
        except OSError as e:
            raise SqlfmtConfigError(
                f"Error opening pyproject.toml config file at {config_path}. {e}"
            ) from e
        except tomllib.TOMLDecodeError as e:
            raise SqlfmtConfigError(
                f"Error decoding pyproject.toml config file at {config_path}. "
                f"Check for invalid TOML. {e}"
            ) from e
        raw_config: Config = pyproject_dict.get("tool", {}).get("sqlfmt", {})
        if "exclude" in raw_config and "exclude_root" not in raw_config:
            raw_config["exclude_root"] = config_path.parent
        return _validate_config(raw_config)


def _validate_config(raw_config: Config) -> Config:
    config = {}
    for k, v in ((k.lower(), v) for k, v in raw_config.items()):
        if k == "dialect":
            _check_value_type("dialect_name", v)
            config["dialect_name"] = v
        elif k not in Mode.__dataclass_fields__:
            raise SqlfmtConfigError(
                f"Config file contains key {k}, which is not a "
                f"supported option. Must be one of "
                f"{_supported_keys()}"
            )
        else:
            _check_value_type(k, v)
            config[k] = v
    return config


def _check_value_type(key: str, value: object) -> None:
    """
    Raises a SqlfmtConfigError if value does not have the type that Mode
    expects for key. Options with other types are not checked.
    """
    expected = Mode.__dataclass_fields__[key].type
    if expected is bool:
        valid = isinstance(value, bool)
        type_name = "a boolean"
    elif expected is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
        type_name = "an integer"
    elif expected is str:
        valid = isinstance(value, str)
        type_name = "a string"
    elif expected == List[str]:
        valid = isinstance(value, list) and all(isinstance(i, str) for i in value)
        type_name = "a list of strings"
    else:
        return
    if not valid:
        raise SqlfmtConfigError(
            f"Config file option {_user_key(key)} must be {type_name}, "
            f"but got {value!r}."
        )


def _supported_keys() -> List[str]:
    """
    Returns the names of the options that a user can set in a config file
    """
    return [_user_key(k) for k in Mode.__dataclass_fields__ if k != "SQL_EXTENSIONS"]


def _user_key(key: str) -> str:
    return "dialect" if key == "dialect_name" else key
