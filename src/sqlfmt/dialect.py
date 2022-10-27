from abc import ABC, abstractmethod
from typing import Dict, List

from sqlfmt.analyzer import Analyzer
from sqlfmt.node_manager import NodeManager
from sqlfmt.rule import JINJA, MAIN, Rule


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the RULES dict to define their own grammar. RULES
    must have a key "main" that contains the rules for the main lexing loop.
    """

    RULES: Dict[str, List[Rule]]
    case_sensitive_names = False

    @abstractmethod
    def get_rules(self) -> Dict[str, List[Rule]]:
        """
        Returns the Dialect's Rules, as a dict keyed by the name of the ruleset,
        e.g., main
        """
        return {
            k: sorted(v, key=lambda rule: rule.priority) for k, v in self.RULES.items()
        }

    def initialize_analyzer(self, line_length: int) -> Analyzer:
        """
        Creates and returns an analyzer that uses the Dialect's rules for lexing
        """
        analyzer = Analyzer(
            line_length=line_length,
            rules=self.get_rules(),
            node_manager=NodeManager(self.case_sensitive_names),
        )
        return analyzer


class Polyglot(Dialect):
    """
    A universal SQL dialect meant to encompass the common usage of at least
    Postgres, MySQL, BigQuery Standard SQL, Snowflake SQL, SparkSQL.
    """

    def __init__(self) -> None:

        self.RULES: Dict[str, List[Rule]] = {
            "main": [*MAIN],
            "jinja": [*JINJA],
        }

    def get_rules(self) -> Dict[str, List[Rule]]:
        return super().get_rules()


class ClickHouse(Polyglot):
    case_sensitive_names = True
