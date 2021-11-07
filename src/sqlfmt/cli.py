from typing import List

import click

from sqlfmt import api
from sqlfmt.mode import Mode


@click.command()
@click.version_option(package_name="shandy-sqlfmt")
@click.option(
    "--check",
    is_flag=True,
    help=(
        "Fail with an exit code of 1 if source files are not formatted to spec."
        "Do not write formatted queries to files"
    ),
)
@click.option(
    "--diff",
    is_flag=True,
    help=(
        "Print a diff of any formatting changes to stdout. Fails like --check"
        "on any changes. Do not write formatted queries to files"
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
@click.option(
    "--no-color",
    is_flag=True,
    help=(
        "Removes color codes from all output, including diffs."
        "Alternatively, set the NO_COLOR environment variable"
    ),
)
@click.option(
    "--force-color",
    is_flag=True,
    help=(
        "sqlfmt output is colorized by default. However, if you have"
        "the NO_COLOR env var set, and still want sqlfmt to colorize"
        "output, you can use --force-color to override the env var"
    ),
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True),
)
@click.pass_context
def sqlfmt(
    ctx: click.Context,
    files: List[str],
    check: bool,
    diff: bool,
    no_color: bool,
    force_color: bool,
    line_length: int,
    verbose: bool,
) -> None:
    """
    sqlfmt is an opinionated CLI tool that formats your sql files
    """
    mode = Mode(
        line_length=line_length,
        check=check,
        diff=diff,
        verbose=verbose,
        _no_color=no_color,
        _force_color=force_color,
    )
    exit_code = api.run(files=files, mode=mode)
    ctx.exit(exit_code)
