import re
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest
from click.testing import CliRunner

from sqlfmt.cli import sqlfmt as sqlfmt_main
from tests.util import copy_config_file_to_dst


def run_cli_command(commands: List[str]) -> subprocess.CompletedProcess:
    process = subprocess.run(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
    )
    return process


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Fails on GHA windows runner, can't repro locally",
)
@pytest.mark.parametrize(
    "cmd",
    [
        "sqlfmt --no-progressbar",
        "python -m sqlfmt --no-progressbar",
    ],
)
def test_click_cli_runner_is_equivalent_to_py_subprocess(
    sqlfmt_runner: CliRunner, cmd: str
) -> None:

    builtin_results = run_cli_command([cmd])
    click_results = sqlfmt_runner.invoke(sqlfmt_main)

    assert builtin_results.returncode == click_results.exit_code
    assert builtin_results.stdout == click_results.stdout
    assert builtin_results.stderr == click_results.stderr

    assert "https://sqlfmt.com" in click_results.stderr
    assert "sqlfmt ." in click_results.stderr


def test_help_command(sqlfmt_runner: CliRunner) -> None:
    # Sally installs sqlfmt; not knowing where to start, she types "sqlfmt --help" into
    # her command line, and sees that it displays the version and a help menu
    help_option = "--help"
    help_results = sqlfmt_runner.invoke(sqlfmt_main, args=help_option)
    assert help_results.exit_code == 0
    assert help_results.stdout.startswith("Usage: sqlfmt")


def test_version_command(sqlfmt_runner: CliRunner) -> None:
    version_option = "--version"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=version_option)
    assert results.exit_code == 0
    assert results.stdout.startswith("sqlfmt, version ")

    semver_pattern = r"\d+\.\d+.\d+"
    match = re.search(semver_pattern, results.stdout)
    assert match, "Semantic version number not in output"


def test_stdin(sqlfmt_runner: CliRunner) -> None:
    input = "select 1"
    results = sqlfmt_runner.invoke(sqlfmt_main, args="-", input=input)
    assert results.exit_code == 0
    assert results.stdout == "select 1\n\n"


def test_preformatted_check(sqlfmt_runner: CliRunner, preformatted_dir: Path) -> None:
    args = f"{preformatted_dir.as_posix()} --check"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0
    assert "passed formatting check" in results.stderr

    args = f"{preformatted_dir.as_posix()}"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args, env={"SQLFMT_CHECK": "1"})
    assert results.exit_code == 0
    assert "passed formatting check" in results.stderr


def test_preformatted_short_lines_env(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    args = f"{preformatted_dir.as_posix()}"
    results = sqlfmt_runner.invoke(
        sqlfmt_main, args=args, env={"SQLFMT_LINE_LENGTH": "1"}
    )
    assert results.exit_code == 0
    print(results.stderr)
    assert "5 files formatted" in results.stderr

    # test that CLI flag overrides ENV VAR
    args = f"{preformatted_dir.as_posix()} -l 88 --check"
    results = sqlfmt_runner.invoke(
        sqlfmt_main, args=args, env={"SQLFMT_LINE_LENGTH": "1"}
    )
    assert results.exit_code == 0
    print(results.stderr)
    assert "passed formatting check" in results.stderr


def test_unformatted_check(sqlfmt_runner: CliRunner, unformatted_dir: Path) -> None:
    args = f"{unformatted_dir.as_posix()} --check"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 1
    assert "failed formatting check" in results.stderr

    args = f"{unformatted_dir.as_posix()}"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args, env={"SQLFMT_CHECK": "1"})
    assert results.exit_code == 1
    assert "failed formatting check" in results.stderr


def test_error_check(sqlfmt_runner: CliRunner, error_dir: Path) -> None:
    args = f"{error_dir.as_posix()} --check"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 2


def test_preformatted_single_process(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    args = f"{preformatted_dir.as_posix()} --single-process"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0


def test_preformatted_config_file(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    # config file sets line length to 100 and enables check mode
    copy_config_file_to_dst("valid_sqlfmt_config.toml", preformatted_dir)
    args = f"{preformatted_dir.as_posix()}"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    # 3 files should fail formatting with longer line length in config
    assert results.exit_code == 1
    assert results.stderr.startswith("3 files failed formatting check")
    # supply CLI args to override config file so checks pass
    args = f"{preformatted_dir.as_posix()} --line-length 88"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0


def test_preformatted_exclude_all(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    args = (
        f"{preformatted_dir.as_posix()} --exclude {preformatted_dir.as_posix()}/*.sql"
    )
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0
    assert results.stderr.startswith("0 files left unchanged")


def test_preformatted_clickhouse(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    args = f"{preformatted_dir.as_posix()} --check --dialect clickhouse"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0


def test_preformatted_no_progressbar(
    sqlfmt_runner: CliRunner, preformatted_dir: Path
) -> None:
    args = f"{preformatted_dir.as_posix()} --check --no-progressbar"
    results = sqlfmt_runner.invoke(sqlfmt_main, args=args)
    assert results.exit_code == 0
