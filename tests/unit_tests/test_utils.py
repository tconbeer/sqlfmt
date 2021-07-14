from pathlib import Path

from sqlfmt.mode import Mode
from sqlfmt.utils import gen_sql_files


def test_file_discovery() -> None:
    p = Path("tests/data/basic_queries/")
    res = list(gen_sql_files(p.iterdir(), Mode()))

    expected = (
        Path("tests/data/basic_queries/001_select_1.sql"),
        Path("tests/data/basic_queries/002_select_from_where.sql"),
    )

    for p in expected:
        assert p in res
