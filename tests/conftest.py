import os
import sys
from itertools import product
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from sqlfmt.analyzer import Analyzer
from sqlfmt.mode import Mode
from tests.util import copy_test_data_to_tmp

# make tests module importable
sys.path.append(os.path.dirname(__file__))


def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    from sqlfmt.cache import clear_cache
    from tests.util import delete_results_dir

    delete_results_dir()
    clear_cache()


@pytest.fixture
def sqlfmt_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def unset_no_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)


@pytest.fixture
def default_mode(unset_no_color_env: None) -> Mode:
    return Mode()


@pytest.fixture
def clickhouse_mode(unset_no_color_env: None) -> Mode:
    return Mode(dialect_name="clickhouse")


@pytest.fixture
def verbose_mode(unset_no_color_env: None) -> Mode:
    return Mode(verbose=True)


@pytest.fixture
def check_mode(unset_no_color_env: None) -> Mode:
    return Mode(check=True)


@pytest.fixture
def verbose_check_mode(unset_no_color_env: None) -> Mode:
    return Mode(check=True, verbose=True)


@pytest.fixture
def diff_mode(unset_no_color_env: None) -> Mode:
    return Mode(diff=True)


@pytest.fixture
def no_color_diff_mode(unset_no_color_env: None) -> Mode:
    return Mode(diff=True, no_color=True)


@pytest.fixture
def reset_cache_mode(unset_no_color_env: None) -> Mode:
    return Mode(reset_cache=True)


@pytest.fixture
def no_progressbar_mode(unset_no_color_env: None) -> Mode:
    return Mode(no_progressbar=True)


@pytest.fixture
def single_process_mode(unset_no_color_env: None) -> Mode:
    return Mode(single_process=True)


@pytest.fixture(params=product([True, False], repeat=4))
def all_output_modes(request: Any, unset_no_color_env: None) -> Mode:
    return Mode(
        check=request.param[0],
        diff=request.param[1],
        single_process=request.param[2],
        no_progressbar=request.param[3],
    )


@pytest.fixture
def default_analyzer(default_mode: Mode) -> Analyzer:
    return default_mode.dialect.initialize_analyzer(default_mode.line_length)


@pytest.fixture
def preformatted_dir(tmp_path: Path) -> Path:
    """
    Copies the directory of preformatted sql files from the unit test
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["fast/preformatted"], tmp_path)
    return test_dir


@pytest.fixture
def unformatted_dir(tmp_path: Path) -> Path:
    """
    Copies the directory of unformatted sql files from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["fast/unformatted"], tmp_path)
    return test_dir


@pytest.fixture
def error_dir(tmp_path: Path) -> Path:
    test_dir = copy_test_data_to_tmp(["fast/errors"], tmp_path)
    return test_dir
