def group(*choices: str) -> str:
    """
    Convenience function for creating grouped alternatives in regex
    """
    return f"({'|'.join(choices)})"


MAYBE_WHITESPACES: str = r"[^\S\n]*"  # any whitespace except newline
NEWLINE: str = r"\r?\n"
EOL = group(NEWLINE, r"$")
