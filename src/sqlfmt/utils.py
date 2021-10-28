from pathlib import Path
from typing import Iterable, Iterator, Optional

import click

from sqlfmt.mode import Mode


def style_output(
    msg: str, fg: Optional[str] = None, bg: Optional[str] = None, bold: bool = False
) -> str:
    # see https://click.palletsprojects.com/en/8.0.x/api/?highlight=style#click.style
    s: str = click.style(msg, fg=fg, bg=bg, bold=bold)
    return s


def display_output(msg: str, err: bool = True) -> None:
    click.echo(msg, err=err)


def gen_sql_files(paths: Iterable[Path], mode: Mode) -> Iterator[Path]:
    for p in paths:
        if p.is_file() and "".join(p.suffixes) in (mode.SQL_EXTENSIONS):
            yield p
        elif p.is_dir():
            yield from (gen_sql_files(p.iterdir(), mode))
