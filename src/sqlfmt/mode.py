import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from sqlfmt.dialect import ClickHouse, Polyglot
from sqlfmt.exception import SqlfmtConfigError


@dataclass
class Mode:
    """
    A Mode is a container for all sqlfmt config, including formatting config and
    report config. For more info on each option, see cli.py
    """

    SQL_EXTENSIONS: List[str] = field(default_factory=lambda: [".sql", ".sql.jinja"])
    dialect_name: str = "polyglot"
    line_length: int = 88
    check: bool = False
    diff: bool = False
    exclude: List[str] = field(default_factory=list)
    exclude_root: Optional[Path] = None
    encoding: str = "utf-8"
    fast: bool = False
    single_process: bool = False
    no_jinjafmt: bool = False
    reset_cache: bool = False
    verbose: bool = False
    quiet: bool = False
    no_progressbar: bool = False
    no_color: bool = False
    force_color: bool = False

    def __post_init__(self) -> None:
        # get the dialect from its name.
        dialects = {
            "polyglot": Polyglot,
            "clickhouse": ClickHouse,
        }
        try:
            self.dialect = dialects[self.dialect_name.lower()]()
        except KeyError:
            raise SqlfmtConfigError(
                f"Mode was created with dialect_name={self.dialect_name}, "
                "which is not supported. Did you mean 'polyglot'?"
            )

    @property
    def color(self) -> bool:
        """
        There are 4 considerations for setting color:
        1. The --force-color option
        2. The --no-color option
        3. The NO_COLOR environment variable
        4. The default behavior, which is to colorize output

        This property checks these flags, in descending order of priority,
        and sets the authoritative flag accordingly

        See no-color.org for details.
        """
        if self.force_color:
            return True
        elif self.no_color:
            return False
        elif os.environ.get("NO_COLOR", False):
            return False
        else:
            return True
