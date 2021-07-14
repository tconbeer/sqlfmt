from sqlfmt.api import format_string
from sqlfmt.mode import Mode


def test_format_empty_string() -> None:
    default_mode = Mode()
    source = expected = ""
    actual = format_string(source, default_mode)
    assert expected == actual
