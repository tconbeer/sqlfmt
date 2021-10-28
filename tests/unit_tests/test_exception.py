from sqlfmt.exception import SqlfmtError


def test_exception_printing() -> None:
    e = SqlfmtError("my test message")
    assert str(e) == "sqlfmt encountered an error: my test message"
