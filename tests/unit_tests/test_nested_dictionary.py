from sqlfmt.api import format_string
from sqlfmt.mode import Mode
from tests.util import read_test_data


def test_handle_nested_dictionary_in_jinja_expression() -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_nested_dictionary/test_nested_dictionary.sql"
    )
    actual = format_string(source_string, mode=Mode(line_length=100))
    assert expected_string == actual


def test_handle_false_positive(default_mode: Mode) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_nested_dictionary/test_false_positive.sql"
    )
    actual = format_string(source_string, mode=default_mode)
    assert expected_string == actual


def test_handle_triple_nested_single_quote_100() -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_nested_dictionary/test_triple_nested_single_quote_100.sql"
    )
    actual = format_string(source_string, mode=Mode(line_length=100))
    assert expected_string == actual


def test_handle_triple_nested_single_quote_default(default_mode: Mode) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_nested_dictionary/test_triple_nested_single_quote_88.sql"
    )
    actual = format_string(source_string, mode=default_mode)
    assert expected_string == actual
