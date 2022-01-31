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
        "Fail with an exit code of 1 if source files are not formatted to spec. "
        "Do not write formatted queries to files"
    ),
)
@click.option(
    "--diff",
    is_flag=True,
    help=(
        "Print a diff of any formatting changes to stdout. Fails like --check "
        "on any changes. Do not write formatted queries to files"
    ),
)
@click.option(
    "--single-process",
    is_flag=True,
    help=(
        "Run sqlfmt in a single process, even when formatting multiple "
        "files. If not set, defaults to multiprocessing using as many "
        "cores as possible"
    ),
)
@click.option(
    "--no-jinjafmt",
    is_flag=True,
    help=(
        "Do not format jinja tags (the code between the curlies). Only necessary "
        "to specify this flag if sqlfmt was installed with the jinjafmt extra, "
        "or if black was already available in this environment"
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
    "-q",
    "--quiet",
    is_flag=True,
    help=("Prints much less information to stderr"),
)
@click.option(
    "--no-color",
    is_flag=True,
    help=(
        "Removes color codes from all output, including diffs. "
        "Alternatively, set the NO_COLOR environment variable"
    ),
)
@click.option(
    "--force-color",
    is_flag=True,
    help=(
        "sqlfmt output is colorized by default. However, if you have "
        "the NO_COLOR env var set, and still want sqlfmt to colorize "
        "output, you can use --force-color to override the env var"
    ),
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, allow_dash=True),
)
@click.pass_context
def sqlfmt(
    ctx: click.Context,
    files: List[str],
    check: bool,
    diff: bool,
    single_process: bool,
    no_jinjafmt: bool,
    no_color: bool,
    force_color: bool,
    line_length: int,
    verbose: bool,
    quiet: bool,
) -> None:
    """
    sqlfmt is a tool that formats your sql files.

    The FILES argument can be one or many paths to sql files (or directories),
    or use "-" to use stdin.

    Exit codes: 0 indicates success, 1 indicates failed check,
    2 indicates a handled exception caused by errors in one or more user code files
    """
    if files:
        mode = Mode(
            line_length=line_length,
            check=check,
            diff=diff,
            single_process=single_process,
            no_jinjafmt=no_jinjafmt,
            verbose=verbose,
            quiet=quiet,
            _no_color=no_color,
            _force_color=force_color,
        )

        report = api.run(files=files, mode=mode)
        report.display_report()

        if report.number_errored > 0:
            exit_code = 2
        elif (mode.check or mode.diff) and report.number_changed > 0:
            exit_code = 1
        else:
            exit_code = 0
    else:
        show_welcome_message()
        exit_code = 0

    ctx.exit(exit_code)


def show_welcome_message() -> None:
    """
    Prints a nice welcome message for new users who might accidentally
    enter `$ sqlfmt` without any arguments
    """
    from sqlfmt.report import display_output, style_output

    art = r"""
               _  __           _
              | |/ _|         | |
     ___  __ _| | |_ _ __ ___ | |_
    / __|/ _` | |  _| '_ ` _ \| __|
    \__ \ (_| | | | | | | | | | |_
    |___/\__, |_|_| |_| |_| |_|\__|
            | |
            |_|"""
    display_output(msg=art)
    message = """
    sqlfmt formats your dbt SQL files so you don't have to.
    For more information, visit http://sqlfmt.com

    To get started, try:
    """
    display_output(msg=message)
    commands = [
        (
            "sqlfmt .",
            "format all files nested in the current dir (note the '.')",
        ),
        (
            "sqlfmt path/to/file.sql",
            "format file.sql only",
        ),
        (
            "sqlfmt . --check",
            "check formatting of all files, exit with code 1 on changes",
        ),
        (
            "sqlfmt . --diff",
            "print diff resulting from formatting all files",
        ),
        (
            "sqlfmt -",
            "format text received through stdin, write result to stdout",
        ),
        (
            "sqlfmt --help",
            "show more options and other usage information",
        ),
    ]
    margin = max([len(cmd) for cmd, _ in commands])
    for cmd, desc in commands:
        styled_cmd = style_output(
            msg=f"{cmd}{' ' * (margin - len(cmd))}",
            fg="white",
            bg="bright_black",
            bold=True,
        )
        display_output(msg=f"    {styled_cmd} {desc}")
    display_output(msg="\n")
