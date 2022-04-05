import shutil
from pathlib import Path
from typing import Any, List

import pytest

from sqlfmt.config import _find_config_file
from tests.util import BASE_DIR


def copy_config_file_to_dst(file_name: str, dst_path: Path) -> Path:
    CONFIG_DIR = BASE_DIR / "config"
    file_path = CONFIG_DIR / file_name
    assert file_path.is_file()

    new_file_path = dst_path / "pyproject.toml"
    shutil.copyfile(file_path, new_file_path)
    return new_file_path


@pytest.fixture(
    params=[
        [""],
        ["subdir"],
        ["subdir", "another"],
        ["model.sql"],
        ["model.sql", "another.sql"],
        ["subdir/model.sql"],
        ["subdir/model.sql", "another_dir"],
        ["subdir/another_dir/yet_another_dir/"],
        ["subdir/another_dir/yet_another_dir/model.sql"],
    ]
)
def files_relpath(request: Any) -> List[str]:
    p: List[str] = request.param
    return p


def test_find_config_file(tmp_path: Path, files_relpath: List[str]) -> None:
    copy_config_file_to_dst("test_load_config_file.toml", tmp_path)

    files = [str(tmp_path / p) for p in files_relpath]
    config_path = _find_config_file(files)
    assert config_path
    assert config_path == tmp_path / "pyproject.toml"


def test_find_config_file_no_file(tmp_path: Path, files_relpath: List[str]) -> None:
    # don't copy the config file

    files = [str(tmp_path / p) for p in files_relpath]
    config_path = _find_config_file(files)
    assert config_path is None


def test_find_config_file_not_in_tree(tmp_path: Path, files_relpath: List[str]) -> None:
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    copy_config_file_to_dst("test_load_config_file.toml", config_dir)

    files = [str(tmp_path / p) for p in files_relpath]
    config_path = _find_config_file(files)
    assert config_path is None
