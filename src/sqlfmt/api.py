from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set

from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.utils import display_output, gen_sql_files


@dataclass
class SqlFormatResult:
    source_path: Optional[Path]
    source_string: str
    formatted_string: Optional[str]


def run(files: List[str], mode: Mode) -> int:
    """
    Runs sqlfmt on all files in list of given paths (files), using the specified mode.
    Yields SqlFormatResults.
    """
    matched_paths: Set[Path] = set()
    for s in files:
        p = Path(s)

        if p.is_file() and p.suffix in (mode.SQL_EXTENSIONS):
            matched_paths.add(p)

        elif p.is_dir():
            matched_paths.update(gen_sql_files(p.iterdir(), mode))

    results = _generate_results(matched_paths, mode)

    for res in results:
        display_output(str(res))

    return 0


def _generate_results(paths: Iterable[Path], mode: Mode) -> Iterator[SqlFormatResult]:
    for p in paths:
        with (open(p, "r")) as f:
            source = f.read()
            formatted = format_string(source, mode)
            yield SqlFormatResult(
                source_path=p, source_string=source, formatted_string=formatted
            )


def format_string(source: str, mode: Mode) -> str:
    raw_query = Query.from_source(source_string=source, mode=mode)
    formatter = QueryFormatter(mode)
    formatted_query = formatter.format(raw_query)
    return str(formatted_query)
