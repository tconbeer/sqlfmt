import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from sqlfmt.analyzer import Analyzer

MAYBE_WHITESPACES: str = r"[^\S\n]*"  # any whitespace except newline


@dataclass
class Rule:
    """
    A lex rule.

    When the analyzer lexes the source string, it applies each Rule in turn,
    in ascending order of priority.

    The Analyzer tries to match the Rule's regex pattern to the current position
    in the source string. If there is a match, the Analyzer calls the Rule's
    action with the arguments (self [the analyzer], source_string, match). The
    Rule's action may mutate the analyzer's buffer (if desired). The action
    must return the position in the source_string where the Analyzer should
    look for the next match.
    """

    name: str
    priority: int  # lower get matched first
    pattern: str
    action: Callable[["Analyzer", str, re.Match], None]

    def __post_init__(self) -> None:
        self.program = re.compile(
            MAYBE_WHITESPACES + self.pattern, re.IGNORECASE | re.DOTALL
        )
