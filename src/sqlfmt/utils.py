from pathlib import Path
from typing import Iterable, Iterator

import click

from sqlfmt.mode import Mode


def display_output(msg: str, err: bool = True) -> None:
    click.echo(msg, err=err)


def gen_sql_files(paths: Iterable[Path], mode: Mode) -> Iterator[Path]:
    for p in paths:
        if p.is_file() and "".join(p.suffixes) in (mode.SQL_EXTENSIONS):
            yield p
        elif p.is_dir():
            yield from (gen_sql_files(p.iterdir(), mode))
