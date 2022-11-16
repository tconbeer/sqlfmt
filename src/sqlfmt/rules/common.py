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
