def group(*choices: str) -> str:
    """
    Convenience function for creating grouped alternatives in regex
    """
    return f"({'|'.join(choices)})"


NEWLINE: str = r"\r?\n"
EOL = group(NEWLINE, r"$")

JINJA_START = group(r"\{[{%#]")

SQL_QUOTED_EXP = group(
    # tripled single quotes (optionally raw/bytes).
    #
    # The body cannot be a lazy .*? — that closes on the FIRST ''' it can reach,
    # so `select '''' || 'x' || ''''` is read as a triple-quoted string starting
    # at the first quote and ending three quotes later, stranding a lone quote
    # that nothing can lex. Matching quote runs explicitly, and refusing a
    # closer that is itself followed by another quote, makes the alternative
    # decline rather than mis-close, so the escaped-single-quote alternative
    # below gets its turn. [^'] rather than [^'\r\n] because these patterns are
    # compiled with re.DOTALL and multi-line triple-quoted strings must keep
    # matching.
    r"(rb?|b|br)?'''(?:[^'](?:[^']|'(?!''))*)?'''(?!')",
    # tripled double quotes follow the same quote-run rule as single quotes.
    r'(rb?|b|br)?"""(?:[^"](?:[^"]|"(?!""))*)?"""(?!")',
    # possibly escaped double quotes
    r'(rb?|b|br|u&|@)?"([^"\\]*(\\.[^"\\]*|""[^"\\]*)*)"',
    # possibly escaped single quotes
    r"(rb?|b|br|u&|x)?'([^'\\]*(\\.[^'\\]*|''[^'\\]*)*)'",
    r"\$(?P<tag>\w*)\$.*?\$(?P=tag)\$",  # pg dollar-delimited strings
    # possibly escaped backtick
    r"`([^`\\]*(\\.[^`\\]*)*)`",
)

SQL_COMMENT_START = r"(?=--|#|//|/\*)"
SQL_COMMENT = group(
    r"--[^\r\n]*",
    r"#[^\r\n]*",
    r"//[^\r\n]*",  # snowflake's js-style double-slash comment
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

PRAGMA_SET_CALL = group(r"pragma", r"set", r"call")
