from pathlib import Path
from typing import List, Tuple

import pytest

from sqlfmt.api import format_string
from sqlfmt.mode import Mode


def read_test_data(relpath: str) -> Tuple[str, str]:
    """reads a test file contents and returns a tuple of strings corresponding to
    the unformatted and formatted examples in the test file. If the test file doesn't
    include a ')))))__SQLFMT_OUTPUT__(((((' sentinel, returns the same string twice
    (as the input is assumed to be pre-formatted). relpath is relative to
    tests/data/"""
    SENTINEL = ")))))__SQLFMT_OUTPUT__((((("
    THIS_DIR = Path(__file__).parent
    TEST_DIR = THIS_DIR.parent
    BASE_DIR = TEST_DIR / "data"

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


@pytest.mark.xfail
def test_100_base_model() -> None:
    p = "general_formatting/100_base_model.sql"
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    assert expected == actual

    second_pass = format_string(actual, mode)

    assert actual == second_pass
