class SqlfmtError(ValueError):
    """
    Generic class for an error encountered when formatting
    user code. Should be caught by api.run for display to the
    user.
    """

    def __str__(self) -> str:
        intro = "sqlfmt encountered an error: "
        message = super().__str__()
        return f"{intro}{message}"


class SqlfmtConfigError(SqlfmtError):
    """
    Raised during opening or parsing a pyproject.toml file
    """

    pass


class SqlfmtParsingError(SqlfmtError):
    """
    Raised during lexing if sqlfmt encounters a token that does
    not match any rules
    """

    pass


class SqlfmtBracketError(SqlfmtError):
    """
    Raised during lexing if sqlfmt encounters mismatched, unterminated,
    or unexpected closing brackets
    """

    pass


class SqlfmtSegmentError(SqlfmtError):
    """
    Raised during merging if a segment is unexpectedly empty
    """

    pass


class SqlfmtEquivalenceError(SqlfmtError):
    """
    Raised during the safety check if the result query does
    not lex to the same tokens as the raw query
    """

    pass


class SqlfmtControlFlowException(Exception):
    """
    Generic exception for exceptions used to manage control
    flow. Should always be caught by the application and
    never raised back to the user
    """

    pass


class InlineCommentException(SqlfmtControlFlowException):
    """
    Raised by the Line class if we try to render a comment
    inline that is too long
    """

    pass


class StopRulesetLexing(SqlfmtControlFlowException):
    """
    Raised by the Analyzer or one of its actions to indicate
    that further lexing should use the previous ruleset
    """

    pass


class CannotMergeException(SqlfmtControlFlowException):
    """
    Raised by the merger if the passed lines cannot be merged
    for any reason
    """

    pass
