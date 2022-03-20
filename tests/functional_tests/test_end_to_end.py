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
        "--check",
        "--check -v",
        "--diff",
        "-v --diff",
        "--check --diff",
        "--no-color",
        "--diff --no-color",
        "-q",
        "--quiet",
        "--check -q",
        "--no-jinjafmt",
    ],
)
def test_end_to_end_preformatted(
    sqlfmt_runner: CliRunner, preformatted_target: Path, options: str
) -> None:

    # CliRunner removes backslashes from strings passed in as args,
    # which makes this test fail when running on windows. We need
    # to format the path as a posix path (with forward slashes)
    # as a workaround.
    args = f"{preformatted_target.as_posix()} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "6 files" in result.stderr

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
        "--check",
        "--check -v",
        "--diff",
        "-v --diff",
        "--diff --check",
        "--check --no-color",
        "--diff --no-color",
        "-q --check",
        "--quiet --check",
        "--check -q",
    ],
)
def test_end_to_end_check_unformatted(
    sqlfmt_runner: CliRunner, unformatted_target: Path, options: str
) -> None:

    # CliRunner removes backslashes from strings passed in as args,
    # which makes this test fail when running on windows. We need
    # to format the path as a posix path (with forward slashes)
    # as a workaround.
    args = f"{unformatted_target.as_posix()} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "16 files" in result.stderr
    assert "failed formatting check" in result.stderr

    if "-q" in options or "--quiet" in options:
        assert "100_select_case.sql" not in result.stderr
    else:
        assert "100_select_case.sql" in result.stderr

    assert result.exit_code == 1


@pytest.mark.parametrize("options", ["", "--check", "--no-color", "--quiet"])
def test_end_to_end_errors(
    sqlfmt_runner: CliRunner, error_target: Path, options: str
) -> None:
    # CliRunner removes backslashes from strings passed in as args,
    # which makes this test fail when running on windows. We need
    # to format the path as a posix path (with forward slashes)
    # as a workaround.
    args = f"{error_target.as_posix()} {options}"
    result = sqlfmt_runner.invoke(sqlfmt_main, args=args)

    assert result
    assert "4 files had errors" in result.stderr
    assert "sqlfmt encountered an error" in result.stderr
    assert "900_bad_token.sql" in result.stderr
    assert result.exit_code == 2


@pytest.mark.parametrize(
    "options,input,expected_stdout,expected_exit",
    [
        ("-", "select    1\n", "select 1\n\n", 0),
        ("-", "select 1\n", "select 1\n\n", 0),
        ("- --check", "select    1\n", "", 1),
        ("- --diff", "select    1\n", "", 1),
        ("- --check", "select 1\n", "", 0),
        ("- --diff", "select 1\n", "", 0),
    ],
)
def test_stdin(
    sqlfmt_runner: CliRunner,
    options: str,
    input: str,
    expected_stdout: str,
    expected_exit: int,
) -> None:
    results = sqlfmt_runner.invoke(sqlfmt_main, args=options, input=input)
    assert results.exit_code == expected_exit
    assert results.stdout == expected_stdout
