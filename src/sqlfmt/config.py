from pathlib import Path
from typing import Dict, List, Optional, Set, Union

Config = Dict[str, Union[bool, int]]


def load_config_file(files: List[str]) -> Config:
    """
    files is a list of resolved, absolute paths (like the ones passed from the
    Click CLI). This finds a pyproject.toml file in the common parent directory
    of files (or in the common parent's parents).
    """
    # find pyproject by taking intersection of parents of files
    # read it using a toml library?
    # validate it?
    config_file_path = _find_config_file(files)

    if config_file_path:
        config: Config = {}  # _load_config_from_path(config_file_path)
    else:
        config = {}

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
