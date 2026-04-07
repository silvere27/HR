import subprocess
import sys


def test_cli_rejects_conflicting_modes():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hr_insights.cli",
            "data/sample_employees.csv",
            "--quality",
            "--hiring-funnel",
        ],
        text=True,
        capture_output=True,
        env={"PYTHONPATH": "src"},
    )
    assert completed.returncode != 0
    assert "not allowed with argument" in completed.stderr
