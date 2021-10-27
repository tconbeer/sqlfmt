from typing import List

import click

from sqlfmt import __version__, api, utils
from sqlfmt.mode import Mode


@click.command()
@click.option(
    "-o",
    "--output",
    type=click.Choice(["update", "check", "diff"], case_sensitive=False),
    default="update",
    help=(
        "Determines the result of running sqlfmt. "
        "update: [default] overwrite the source files with the formatted sql. "
        "check: fail with exit_code=1 if source files are not formatted to spec. "
        "diff: print a diff of any formatting changes to stdout"
    ),
)
@click.option(
    "-l",
    "--line-length",
    default=88,
    type=int,
    help=("The maximum line length allowed in output files. Default is 88"),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help=("Prints more information to stderr"),
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True),
)
@click.pass_context
def sqlfmt(
    ctx: click.Context, files: List[str], output: str, line_length: int, verbose: bool
) -> None:
    """
    sqlfmt is an opinionated CLI tool that formats your sql files
    """
    utils.display_output(f"Running sqlfmt {__version__}")

    mode = Mode(line_length=line_length, output=output, verbose=verbose)

    exit_code = api.run(files=files, mode=mode)
    ctx.exit(exit_code)
