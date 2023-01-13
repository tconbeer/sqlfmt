def group(*choices: str) -> str:
    """
    Convenience function for creating grouped alternatives in regex
    """
    return f"({'|'.join(choices)})"


NEWLINE: str = r"\r?\n"
EOL = group(NEWLINE, r"$")

SQL_QUOTED_EXP = group(
    # tripled single quotes (optionally raw/bytes)
    r"(rb?|b|br)?'''.*?'''",
    # tripled double quotes
    r'(rb?|b|br)?""".*?"""',
    # possibly escaped double quotes
    r'(rb?|b|br|u&|@)?"([^"\\]*(\\.[^"\\]*|""[^"\\]*)*)"',
    # possibly escaped single quotes
    r"(rb?|b|br|u&|x)?'([^'\\]*(\\.[^'\\]*|''[^'\\]*)*)'",
    r"\$(?P<tag>\w*)\$.*?\$(?P=tag)\$",  # pg dollar-delimited strings
    # possibly escaped backtick
    r"`([^`\\]*(\\.[^`\\]*)*)`",
)

SQL_COMMENT = group(
    r"--[^\r\n]*",
    r"#[^\r\n]*",
    r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # simple block comment
)

CREATE_FUNCTION = (
    r"create(\s+or\s+replace)?(\s+temp(orary)?)?(\s+secure)?"
    r"(\s+external)?(\s+table)?"
    r"\s+function(\s+if\s+not\s+exists)?"
)
ALTER_DROP_FUNCTION = r"(alter|drop)\s+function(\s+if\s+exists)?"

CREATE_WAREHOUSE = r"create(\s+or\s+replace)?\s+warehouse(\s+if\s+not\s+exists)?"
ALTER_WAREHOUSE = r"alter\s+warehouse(\s+if\s+exists)?"

CREATE_CLONABLE = (
    r"create(\s+or\s+replace)?\s+"
    + group(
        r"database",
        r"schema",
        r"table",
        r"stage",
        r"file\s+format",
        r"sequence",
        r"stream",
        r"task",
    )
    + r"(\s+if\s+not\s+exists)?"
)
