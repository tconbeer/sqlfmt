from abc import ABC, abstractmethod
from functools import partial
from typing import List

from sqlfmt import actions
from sqlfmt.analyzer import Analyzer
from sqlfmt.node_manager import NodeManager
from sqlfmt.rule import Rule
from sqlfmt.rules import MAIN
from sqlfmt.rules.common import NEWLINE, group
from sqlfmt.tokens import TokenType


class Dialect(ABC):
    """
    Abstract class for a SQL dialect.

    Each dialect should override the RULES dict to define their own grammar. RULES
    must have a key "main" that contains the rules for the main lexing loop.
    """

    RULES: List[Rule]
    case_sensitive_names = False

    @abstractmethod
    def get_rules(self) -> List[Rule]:
        """
        Returns the Dialect's Rules, sorted by priority
        """
        return sorted(self.RULES, key=lambda rule: rule.priority)

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
        self.RULES = MAIN

    def get_rules(self) -> List[Rule]:
        return super().get_rules()


class ClickHouse(Polyglot):
    case_sensitive_names = True


class DuckDB(Polyglot):
    """
    DuckDB dialect. In DuckDB, // is the integer division operator,
    not a comment marker.
    """

    def __init__(self) -> None:
        super().__init__()
        # Replace the comment rule to exclude // comments
        # and add a rule for the // operator
        modified_rules = []
        for rule in self.RULES:
            if rule.name == "comment":
                # Replace with a comment rule that excludes //
                modified_rules.append(
                    Rule(
                        name="comment",
                        priority=300,
                        pattern=group(
                            r"--[^\r\n]*",
                            r"#[^\r\n]*",
                            r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/",  # block comment
                        ),
                        action=actions.add_comment_to_buffer,
                    )
                )
            else:
                modified_rules.append(rule)
        
        # Add the // operator rule with priority 299 (before comments at 300)
        modified_rules.append(
            Rule(
                name="duckdb_int_div",
                priority=299,
                pattern=group(r"//"),
                action=partial(
                    actions.add_node_to_buffer, token_type=TokenType.OPERATOR
                ),
            )
        )
        self.RULES = modified_rules

    def get_rules(self) -> List[Rule]:
        return super().get_rules()
