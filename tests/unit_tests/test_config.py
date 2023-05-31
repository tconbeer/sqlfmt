import os
from pathlib import Path
from typing import Any, List

import pytest

from sqlfmt.config import _find_config_file, _get_common_parents, _load_config_from_path
from sqlfmt.exception import SqlfmtConfigError
from tests.util import copy_config_file_to_dst


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
def files_relpath(request: Any) -> List[Path]:
    params: List[str] = request.param
    return [Path(p) for p in params]


def test_find_config_file(tmp_path: Path, files_relpath: List[Path]) -> None:
    copy_config_file_to_dst("valid_sqlfmt_config.toml", tmp_path)

    files = [tmp_path / p for p in files_relpath]
    search_paths = _get_common_parents(files)
    assert tmp_path in search_paths
    config_path = _find_config_file(search_paths)
    assert config_path
    assert config_path == tmp_path / "pyproject.toml"


def test_find_config_file_no_file(tmp_path: Path, files_relpath: List[Path]) -> None:
    # don't copy the config file

    files = [tmp_path / p for p in files_relpath]
    search_paths = _get_common_parents(files)
    assert tmp_path in search_paths
    config_path = _find_config_file(search_paths)
    assert config_path is None


def test_find_config_file_not_in_tree(
    tmp_path: Path, files_relpath: List[Path]
) -> None:
    # put the config file outside the tree defined by files, so
    # we shouldn't find it
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    copy_config_file_to_dst("valid_sqlfmt_config.toml", config_dir)

    files = [tmp_path / p for p in files_relpath]
    search_paths = _get_common_parents(files)
    assert tmp_path in search_paths
    config_path = _find_config_file(search_paths)
    assert config_path is None


def test_find_config_file_relative_and_absolute(
    tmp_path: Path, files_relpath: List[Path]
) -> None:
    # Only check the cases where we are providing more than one path
    if len(files_relpath) == 1:
        return

    current_dir = os.getcwd()
    copy_config_file_to_dst("valid_sqlfmt_config.toml", tmp_path)

    try:
        os.chdir(tmp_path)

        files = [tmp_path / files_relpath[0], files_relpath[1]]
        search_paths = _get_common_parents(files)
        assert tmp_path in search_paths
        config_path = _find_config_file(search_paths)
        assert config_path
        assert config_path == tmp_path / "pyproject.toml"
    finally:
        os.chdir(current_dir)


def test_load_config_from_path(tmp_path: Path) -> None:
    copy_config_file_to_dst("valid_sqlfmt_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "pyproject.toml")
    assert config
    assert config["line_length"] == 100
    assert config["check"] is True
    assert config.get("name", "does not exist") == "does not exist"


def test_load_config_from_path_minimal_config(tmp_path: Path) -> None:
    copy_config_file_to_dst("exclude_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "pyproject.toml")
    assert config
    assert config["exclude"] == ["target/**/*", "dbt_packages/**/*"]


def test_load_config_from_path_invalid_toml(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    with pytest.raises(SqlfmtConfigError) as excinfo:
        _ = _load_config_from_path(tmp_path / "pyproject.toml")

    assert "Check for invalid TOML" in str(excinfo.value)


def test_load_config_from_path_invalid_key(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_key_config.toml", tmp_path)
    with pytest.raises(SqlfmtConfigError) as excinfo:
        _ = _load_config_from_path(tmp_path / "pyproject.toml")

    assert "foo" in str(excinfo.value)


def test_load_config_from_path_dialect(tmp_path: Path) -> None:
    copy_config_file_to_dst("dialect_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "pyproject.toml")
    assert config
    assert config["dialect_name"] == "clickhouse"


def test_load_config_from_path_dialect_name(tmp_path: Path) -> None:
    copy_config_file_to_dst("dialect_name_config.toml", tmp_path)
    config = _load_config_from_path(tmp_path / "pyproject.toml")
    assert config
    assert config["dialect_name"] == "clickhouse"


def test_load_config_from_missing_file(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    with pytest.raises(SqlfmtConfigError) as excinfo:
        _ = _load_config_from_path(tmp_path / "not_pyproject.toml")

    assert "Error opening pyproject.toml" in str(excinfo.value)


def test_load_config_from_None(tmp_path: Path) -> None:
    copy_config_file_to_dst("invalid_toml_config.toml", tmp_path)
    config = _load_config_from_path(None)
    assert config == {}
