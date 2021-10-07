from pathlib import Path
from typing import List, Tuple

import pytest

from sqlfmt.api import format_string
from sqlfmt.mode import Mode

THIS_DIR = Path(__file__).parent
TEST_DIR = THIS_DIR.parent
BASE_DIR = TEST_DIR / "data"


def read_test_data(relpath: str) -> Tuple[str, str]:
    """reads a test file contents and returns a tuple of strings corresponding to
    the unformatted and formatted examples in the test file. If the test file doesn't
    include a ')))))__SQLFMT_OUTPUT__(((((' sentinel, returns the same string twice
    (as the input is assumed to be pre-formatted). relpath is relative to
    tests/data/"""
    SENTINEL = ")))))__SQLFMT_OUTPUT__((((("

    test_path = BASE_DIR / relpath

    with open(test_path, "r") as test_file:
        lines = test_file.readlines()

    source_query: List[str] = []
    formatted_query: List[str] = []

    target = source_query

    for line in lines:
        if line.rstrip() == SENTINEL:
            target = formatted_query
            continue
        target.append(line)

    if source_query and not formatted_query:
        formatted_query = source_query[:]

    return "".join(source_query).strip() + "\n", "".join(formatted_query).strip() + "\n"


def check_formatting(expected: str, actual: str) -> None:

    try:
        assert (
            expected == actual
        ), "Formatting error. Output file written to tests/.results/"
    except AssertionError as e:
        import inspect

        caller = inspect.stack()[1].function
        results_dir = p = TEST_DIR / ".results"
        results_dir.mkdir(exist_ok=True)
        p = results_dir / (caller + ".sql")
        with open(p, "w") as f:
            f.write(actual)
        raise e


@pytest.mark.parametrize(
    "p",
    [
        "basic_queries/001_select_1.sql",
        "basic_queries/002_select_from_where.sql",
        pytest.param("basic_queries/003_select_case.sql", marks=pytest.mark.xfail),
        "basic_queries/004_with_select.sql",
        pytest.param("basic_queries/005_literals.sql", marks=pytest.mark.xfail),
    ],
)
def test_basic_queries(p: str) -> None:
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    check_formatting(expected, actual)

    second_pass = format_string(actual, mode)
    check_formatting(expected, second_pass)


@pytest.mark.xfail
def test_100_base_model() -> None:
    p = "general_formatting/100_base_model.sql"
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    check_formatting(expected, actual)

    second_pass = format_string(actual, mode)

    check_formatting(expected, second_pass)
