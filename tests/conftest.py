import os
import sys
from typing import Any

import pytest
from click.testing import CliRunner

from sqlfmt.mode import Mode

# make tests module importable
sys.path.append(os.path.dirname(__file__))


def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    from tests.util import delete_results_dir

    delete_results_dir()


@pytest.fixture
def sqlfmt_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def default_mode() -> Mode:
    return Mode()


@pytest.fixture
def verbose_mode() -> Mode:
    return Mode(verbose=True)


@pytest.fixture
def check_mode() -> Mode:
    return Mode(output="check")


@pytest.fixture
def verbose_check_mode() -> Mode:
    return Mode(output="check", verbose=True)


@pytest.fixture
def diff_mode() -> Mode:
    return Mode(output="diff")


@pytest.fixture(params=["update", "check", "diff"])
def all_output_modes(request: Any) -> Mode:
    return Mode(output=request.param)
