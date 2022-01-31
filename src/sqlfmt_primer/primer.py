import shutil
import timeit
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

import click
from git import Repo
from platformdirs import user_cache_dir

from sqlfmt.api import run
from sqlfmt.cache import get_cache_file
from sqlfmt.mode import Mode


@dataclass
class SQLProject:
    name: str
    git_url: str
    git_ref: str
    expected_changed: int
    expected_unchanged: int
    expected_errored: int
    sub_directory: Optional[Path] = None


def get_projects() -> List[SQLProject]:
    projects = [
        SQLProject(
            name="gitlab",
            git_url="https://gitlab.com/gitlab-data/analytics.git",
            git_ref="7161e509b62f53344f19de80d40db2bdba190806",  # Nov 12, 2021
            expected_changed=1857,
            expected_unchanged=7,
            expected_errored=0,
            sub_directory=Path("transform/snowflake-dbt/models"),
        ),
        SQLProject(
            name="rittman",
            git_url="https://github.com/rittmananalytics/ra_data_warehouse.git",
            git_ref="ecde71faa9a4400d864ad2e484a4ac478298e53a",  # v1.2.1
            expected_changed=212,
            expected_unchanged=0,
            expected_errored=4,  # true mismatching brackets
            sub_directory=Path("models"),
        ),
        SQLProject(
            name="http_archive",
            git_url="https://github.com/HTTPArchive/almanac.httparchive.org.git",
            git_ref="db9fd2e1405a549c96ae5091b571989f13a8a539",  # Nov 14, 2021
            expected_changed=1631,
            expected_unchanged=0,
            expected_errored=0,
            sub_directory=Path("sql"),
        ),
        SQLProject(
            name="aqi",
            git_url="https://github.com/tconbeer/aqi_livibility_analysis.git",
            git_ref="8004f3383897d9066e3167fdfddcdd4c8418b7ea",  # sqlfmt 0.5.0
            expected_changed=0,
            expected_unchanged=7,
            expected_errored=0,
            sub_directory=Path("src/aqi_dbt/models"),
        ),
        SQLProject(
            name="jaffle_shop",
            git_url="https://github.com/tconbeer/jaffle_shop.git",
            git_ref="4a860150136dc74c4cdb966540de35f4e24f6a09",  # sqlfmt 0.5.0
            expected_changed=0,
            expected_unchanged=5,
            expected_errored=0,
            sub_directory=Path(""),
        ),
        SQLProject(
            name="dbt_utils",
            git_url="https://github.com/dbt-labs/dbt-utils.git",
            git_ref="51ed999a44fcc7f9f502be11e5f190f5bc84ba4b",  # Jan 17, 2022
            expected_changed=114,
            expected_unchanged=0,
            expected_errored=1,
            sub_directory=Path(""),
        ),
    ]
    return projects


@click.command()
@click.argument("project_names", nargs=-1)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help=("Does not print sqlfmt report to stderr"),
)
@click.option(
    "-k",
    "--reset-cache",
    is_flag=True,
    help=("Always does a fresh clone from project's repo."),
)
@click.option(
    "--single-process",
    is_flag=True,
    help=("Run sqlfmt in a single process. Useful for profiling"),
)
@click.pass_context
def sqlfmt_primer(
    ctx: click.Context,
    quiet: bool,
    reset_cache: bool,
    single_process: bool,
    project_names: List[str],
) -> None:
    """
    Run sqlfmt against one or many projects.

    With no arguments, runs against all projects. Otherwise, valide PROJECT NAMES
    are currently: "aqi", "gitlab", "rittman", and "http_archive"
    """

    all_projects = get_projects()
    all_names = [project.name for project in all_projects]
    if project_names:
        for proj_name in project_names:
            if proj_name not in all_names:
                click.echo(f"FATAL: {proj_name} not in known projects: {all_names}")
                ctx.exit(2)

    # ensure we have sqlfmt and git installed
    git = shutil.which("git")
    assert git, "git must be installed before running primer"

    if not project_names:
        projects = all_projects
    else:
        projects = [
            project for project in all_projects if project.name in project_names
        ]

    mode = Mode(quiet=True, check=True, single_process=single_process)
    exit_code = 0
    clear_sqlfmt_cache()

    with TemporaryDirectory() as working_dir:
        for project in projects:

            target_dir = get_project_source_tree(project, reset_cache, working_dir)

            click.echo(f"Running sqlfmt on {project.name}", err=True)
            start_time = timeit.default_timer()
            report = run(files=[str(target_dir)], mode=mode)
            end_time = timeit.default_timer()
            number_formatted = (
                report.number_changed + report.number_unchanged + report.number_errored
            )
            time_elapsed = end_time - start_time
            click.echo(
                (
                    f"Run completed in {time_elapsed:.2f} seconds "
                    f"({number_formatted / time_elapsed:.1f} files/sec)"
                ),
                err=True,
            )

            if not quiet:
                report.display_report()

            if report.number_changed != project.expected_changed:
                click.echo(
                    (
                        f"Changed:: Expected: "
                        f"{project.expected_changed}, Actual: {report.number_changed}"
                    ),
                    err=True,
                )
            if report.number_unchanged != project.expected_unchanged:
                click.echo(
                    (
                        f"Unchanged:: Expected: "
                        f"{project.expected_unchanged}, "
                        f"Actual: {report.number_unchanged}"
                    ),
                    err=True,
                )
            if report.number_errored != project.expected_errored:
                click.echo(
                    (
                        f"Errored:: Expected: "
                        f"{project.expected_errored}, Actual: {report.number_errored}"
                    ),
                    err=True,
                )

            exit_code = (
                exit_code
                or report.number_changed != project.expected_changed
                or report.number_unchanged != project.expected_unchanged
                or report.number_errored != project.expected_errored
            )

    click.echo(f"Exiting with code {exit_code:d}", err=True)
    ctx.exit(exit_code)


def get_project_source_tree(
    project: SQLProject, reset_cache: bool, working_dir: str
) -> Path:
    """
    Returns a Path to a directory containing a project's source tree. Defaults to
    using a cached copy, but will clone a repo and checkout a specific ref if the
    cache does not exist or if reset_cache is passed (in this case, it copies the
    newly-checked-out tree to the cache)
    """

    cache_dir = Path(user_cache_dir(appname="sqlfmt_primer"))
    proj_cache_dir = cache_dir / project.name / project.git_ref

    if reset_cache or not proj_cache_dir.exists():
        click.echo(f"Cloning {project.name}", err=True)
        target_dir = clone_and_checkout(project, working_dir)
        shutil.copytree(target_dir, proj_cache_dir, dirs_exist_ok=True)
        return target_dir
    else:
        click.echo(f"Using cached files for {project.name}", err=True)
        return proj_cache_dir


def clone_and_checkout(project: SQLProject, working_dir: str) -> Path:
    """
    Clone a project into a local dir, and checkout its ref.
    Returns the local directory containing the source tree
    """
    repo_dir = Path(working_dir) / project.name
    repo = Repo.clone_from(url=project.git_url, to_path=repo_dir)
    head = repo.create_head("sqlfmt", commit=project.git_ref)
    head.checkout(force=True)
    target_dir = repo_dir / project.sub_directory if project.sub_directory else repo_dir
    assert target_dir.exists(), f"Failed to clone repo {project.name}"
    return target_dir


def clear_sqlfmt_cache() -> None:
    """
    Deletes the cache file from the disk, if it exists. Called before
    each primer run to ensure we're formatting every file every time.
    """
    p = get_cache_file()
    try:
        p.unlink()
    except FileNotFoundError:
        pass
