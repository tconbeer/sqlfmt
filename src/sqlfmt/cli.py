from typing import List

import click

from sqlfmt import __version__, utils


@click.command()
@click.option(
    "-l",
    "--line-length",
    default=88,
    type=int,
    help=("The maximum line length allowed in output files. Default is 88"),
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True),
)
def sqlfmt(files: List[str], line_length: int) -> None:
    """
    sqlfmt is an opinionated CLI tool that formats your sql files
    """
    utils.display_output(f"Running sqlfmt {__version__}")

    # call API method
    # try:
    #     _ = api.run()
    # except exceptions.ShandyConfigError as cfg:
    #     raise click.ClickException(str(cfg))
