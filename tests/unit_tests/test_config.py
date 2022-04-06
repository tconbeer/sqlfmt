import shutil
from pathlib import Path
from typing import Any, List

import pytest

from sqlfmt.config import _find_config_file, _load_config_from_path
from sqlfmt.exception import SqlfmtConfigError
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
    copy_config_file_to_dst("valid_sqlfmt_config.toml", tmp_path)

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
    # put the config file outside the tree defined by files, so
    # we shouldn't find it
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    copy_config_file_to_dst("valid_sqlfmt_config.toml", config_dir)

    files = [str(tmp_path / p) for p in files_relpath]
    config_path = _find_config_file(files)
    assert config_path is None


def test_load_config_from_path(tmp_path: Path) -> None:
    copy_config_file_to_dst("valid_sqlfmt_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "pyproject.toml")
    assert config
    assert config["line_length"] == 100
    assert config["check"] is True
    assert config.get("name", "does not exist") == "does not exist"


def test_load_config_from_path_invalid(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    with pytest.raises(SqlfmtConfigError) as excinfo:
        _ = _load_config_from_path(tmp_path / "pyproject.toml")

    assert "Check for invalid TOML" in str(excinfo.value)


def test_load_config_from_missing_file(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "not_pyproject.toml")
    assert config == {}


def test_load_config_from_None(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    config = _load_config_from_path(None)
    assert config == {}
