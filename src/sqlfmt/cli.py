from pathlib import Path
from typing import List, Union

import click

from sqlfmt import api
from sqlfmt.config import load_config_file
from sqlfmt.mode import Mode


@click.command()
@click.version_option(package_name="shandy-sqlfmt")
@click.option(
    "--check",
    envvar="SQLFMT_CHECK",
    is_flag=True,
    help=(
        "Fail with an exit code of 1 if source files are not formatted to spec. "
        "Do not write formatted queries to files."
    ),
)
@click.option(
    "--diff",
    envvar="SQLFMT_DIFF",
    is_flag=True,
    help=(
        "Print a diff of any formatting changes to stdout. Fails like --check "
        "on any changes. Do not write formatted queries to files."
    ),
)
@click.option(
    "--exclude",
    envvar="SQLFMT_EXCLUDE",
    multiple=True,
    help=(
        "A string that is passed to glob.glob as a pathname; any matching files "
        "returned by glob will be excluded from FILES and not formatted. Note "
        "that glob is relative to the current working directory when sqlfmt is "
        "called. To exclude multiple globs, repeat the --exclude option."
    ),
)
@click.option(
    "--single-process",
    envvar="SQLFMT_SINGLE_PROCESS",
    is_flag=True,
    help=(
        "Run sqlfmt in a single process, even when formatting multiple "
        "files. If not set, defaults to multiprocessing using as many "
        "cores as possible."
    ),
)
@click.option(
    "-k",
    "--reset-cache",
    envvar="SQLFMT_RESET_CACHE",
    is_flag=True,
    help=(
        "Clear the sqlfmt cache before running, effectively forcing sqlfmt "
        "to operate on every file. Will slow down runs."
    ),
)
@click.option(
    "--no-jinjafmt",
    envvar="SQLFMT_NO_JINJAFMT",
    is_flag=True,
    help=(
        "Do not format jinja tags (the code between the curlies). Only necessary "
        "to specify this flag if sqlfmt was installed with the jinjafmt extra, "
        "or if black was already available in this environment."
    ),
)
@click.option(
    "-l",
    "--line-length",
    envvar="SQLFMT_LINE_LENGTH",
    default=88,
    type=int,
    help=("The maximum line length allowed in output files. Default is 88."),
)
@click.option(
    "-v",
    "--verbose",
    envvar="SQLFMT_VERBOSE",
    is_flag=True,
    help=("Prints more information to stderr."),
)
@click.option(
    "-q",
    "--quiet",
    envvar="SQLFMT_QUIET",
    is_flag=True,
    help=("Prints much less information to stderr."),
)
@click.option(
    "--no-progressbar",
    envvar="SQLFMT_NO_PROGRESSBAR",
    is_flag=True,
    help=("Never prints a progressbar to stderr."),
)
@click.option(
    "--no-color",
    envvar="SQLFMT_NO_COLOR",
    is_flag=True,
    help=(
        "Removes color codes from all output, including diffs. "
        "Alternatively, set the NO_COLOR environment variable. "
        "See https://no-color.org/ for more details."
    ),
)
@click.option(
    "--force-color",
    envvar="SQLFMT_FORCE_COLOR",
    is_flag=True,
    help=(
        "sqlfmt output is colorized by default. However, if you have "
        "the NO_COLOR env var set, and still want sqlfmt to colorize "
        "output, you can use --force-color to override the env var."
    ),
)
@click.option(
    "-d",
    "--dialect",
    "dialect_name",
    envvar="SQLFMT_DIALECT",
    type=click.Choice(["polyglot", "clickhouse"], case_sensitive=False),
    default="polyglot",
    help=(
        "The SQL dialect for the target files. Nearly all dialects are supported "
        "by the default polyglot dialect. Select the ClickHouse dialect to respect "
        "case sensitivity in function, field, and alias names."
    ),
)
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
)
@click.pass_context
def sqlfmt(
    ctx: click.Context, files: List[Path], **kwargs: Union[bool, int, List[str], str]
) -> None:
    """
    sqlfmt formats your dbt SQL files so you don't have to.

    The FILES argument can be one or many paths to sql files (or directories),
    or use "-" to use stdin.

    Exit codes: 0 indicates success, 1 indicates failed check,
    2 indicates a handled exception caused by errors in one or more user code files.

    https://sqlfmt.com for documentation and more information.
    """
    if files:
        config = load_config_file(files)
        non_default_options = {
            k: v
            for k, v in kwargs.items()
            if ctx.get_parameter_source(k).name != "DEFAULT"  # type: ignore
        }
        config.update(non_default_options)
        mode = Mode(**config)  # type: ignore

        matched_files = api.get_matching_paths(files, mode=mode)
        progress_bar, progress_callback = api.initialize_progress_bar(
            total=len(matched_files), mode=mode
        )

        report = api.run(files=matched_files, mode=mode, callback=progress_callback)

        progress_bar.close()
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
    For more information, visit https://sqlfmt.com

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
