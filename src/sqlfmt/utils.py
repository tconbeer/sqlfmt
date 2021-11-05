from typing import Optional

import click


def style_output(
    msg: str, fg: Optional[str] = None, bg: Optional[str] = None, bold: bool = False
) -> str:
    # see https://click.palletsprojects.com/en/8.0.x/api/?highlight=style#click.style
    s: str = click.style(msg, fg=fg, bg=bg, bold=bold)
    return s


def display_output(msg: str, err: bool = True) -> None:
    click.echo(msg, err=err)
