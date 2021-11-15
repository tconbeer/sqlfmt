import shutil
import timeit
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

import click
from git import Repo

from sqlfmt.api import run
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
            expected_changed=1786,
            expected_unchanged=76,
            expected_errored=2,  # unquoted field named end
            sub_directory=Path("transform/snowflake-dbt/models"),
        ),
        SQLProject(
            name="rittman",
            git_url="https://github.com/rittmananalytics/ra_data_warehouse.git",
            git_ref="ecde71faa9a4400d864ad2e484a4ac478298e53a",  # v1.2.1
            expected_changed=206,
            expected_unchanged=0,
            expected_errored=10,  # 6 will be resolved if we support backticks
            sub_directory=Path("models"),
        ),
        SQLProject(
            name="http_archive",
            git_url="https://github.com/HTTPArchive/almanac.httparchive.org.git",
            git_ref="db9fd2e1405a549c96ae5091b571989f13a8a539",  # Nov 14, 2021
            expected_changed=0,
            expected_unchanged=0,
            expected_errored=1631,  # caused by comments with #
            sub_directory=Path("sql"),
        ),
        SQLProject(
            name="aqi",
            git_url="https://github.com/tconbeer/aqi_livibility_analysis.git",
            git_ref="6ef50aa998794837d436abd3676fe46a19de44e4",  # Oct 1, 2021
            expected_changed=6,
            expected_unchanged=0,
            expected_errored=1,  # caused by comments with #
            sub_directory=Path("src/aqi_dbt/models"),
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
@click.pass_context
def sqlfmt_primer(ctx: click.Context, project_names: List[str]) -> None:
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

    mode = Mode(quiet=True, check=True)
    exit_code = 0

    with TemporaryDirectory() as working_dir:
        for project in projects:

            click.echo(f"Cloning {project.name}", err=True)
            target_dir = clone_and_checkout(project, working_dir)

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

    click.echo(f"Exiting with code {exit_code}", err=True)
    ctx.exit(exit_code)


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
