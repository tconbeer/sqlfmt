import pytest

from sqlfmt.api import format_string
from sqlfmt.mode import Mode
from tests.test_utils import check_formatting, read_test_data


@pytest.mark.parametrize(
    "p",
    [
        "basic_queries/001_select_1.sql",
        "basic_queries/002_select_from_where.sql",
        pytest.param("basic_queries/003_select_case.sql", marks=pytest.mark.xfail),
        "basic_queries/004_with_select.sql",
        "basic_queries/005_literals.sql",
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
