class SqlfmtError(ValueError):
    """
    Generic class for an error encountered when formatting
    user code.
    """

    def __str__(self) -> str:
        message = super().__str__()
        return f"sqlfmt encountered an error: {message}"
