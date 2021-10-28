from pathlib import Path

import pytest
from click.testing import CliRunner

from sqlfmt.cli import sqlfmt as sqlfmt_main
from tests.util import copy_test_data_to_tmp


@pytest.fixture
def preformatted_target(tmp_path: Path) -> Path:
    """
    Copies the parameterized list of files/directories from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["preformatted"], tmp_path)
    return test_dir


@pytest.fixture
def unformatted_target(tmp_path: Path) -> Path:
    """
    Copies the parameterized list of files/directories from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["unformatted"], tmp_path)
    return test_dir


@pytest.fixture
def error_target(tmp_path: Path) -> Path:
    """
    Copies the parameterized list of files/directories from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["errors"], tmp_path)
    return test_dir


@pytest.mark.parametrize(
    "options",
    [
        "",
        "--verbose",
        "--line-length 88",
        "-l 88",
        "--output update",
        "-o update",
        "--output check",
        "-o check",
        "-o check -v",
        "--output diff",
        "-o diff",
        "-v -o diff",
    ],
)
def test_end_to_end_preformatted(
    sqlfmt_runner: CliRunner, preformatted_target: Path, options: str
) -> None:

    args = f"{preformatted_target} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "4 files" in result.stderr

    if "check" in options or "diff" in options:
        assert "passed formatting check" in result.stderr
    else:
        assert "left unchanged" in result.stderr

    if "-v" in options or "--verbose" in options:
        assert "001_select_1.sql" in result.stderr

    assert result.exit_code == 0


@pytest.mark.parametrize(
    "options",
    [
        "--output check",
        "-o check",
        "-o check -v",
        "--output diff",
        "-o diff",
        "-v -o diff",
    ],
)
def test_end_to_end_check_unformatted(
    sqlfmt_runner: CliRunner, unformatted_target: Path, options: str
) -> None:

    args = f"{unformatted_target} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "3 files" in result.stderr

    assert "failed formatting check" in result.stderr

    assert result.exit_code == 1


@pytest.mark.parametrize("options", ["", "-o check"])
def test_end_to_end_errors(
    sqlfmt_runner: CliRunner, error_target: Path, options: str
) -> None:
    args = f"{error_target} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "4 files had errors" in result.stderr

    assert "sqlfmt encountered an error" in result.stderr
