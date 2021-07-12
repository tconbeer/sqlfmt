import subprocess
from typing import List


def run_cli_command(commands: List[str]) -> subprocess.CompletedProcess:
    process = subprocess.run(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return process


def test_basic_project() -> None:

    # Sally runs sqlfmt on a directory
    run_command = [
        "sqlfmt",
        "./tests/data/basic_queries/001_select_1.sql",
        "--line-length",
        "88",
    ]
    run_results = run_cli_command(run_command)
    assert run_results.returncode == 0
