"""Run the baseline, one guard mutation, and the restored case in a scratch copy."""

from pathlib import Path
from shutil import copytree
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory

from scripts.sqlite_worker import ROOT

GUARD = "AND d.capacity - d.reserved >= ?"
MUTANT = "AND d.capacity - d.reserved > ?"
TEST = "tests.test_integration_axis5.IntegrationAxis5.test_it01_last_seats"


def main():
    with TemporaryDirectory(prefix="mingo-axis5-") as scratch:
        target = Path(scratch)
        for item in ("backend", "Database", "scripts", "tests"):
            copytree(ROOT / item, target / item, ignore=lambda _path, _names: {"__pycache__"})
        repository = target / "backend" / "repositories.py"
        original = repository.read_text(encoding="utf-8")
        assert original.count(GUARD) == 1

        def check_case():
            return run([executable, "-B", "-m", "unittest", TEST],
                       cwd=target, capture_output=True, text=True, timeout=30)

        baseline = check_case()
        assert baseline.returncode == 0, baseline.stderr
        print("Baseline >=: IT-01 PASS.")
        repository.write_text(original.replace(GUARD, MUTANT), encoding="utf-8")
        failed = check_case()
        assert failed.returncode == 1 and "409 != 201" in failed.stderr, failed.stderr
        print("Mutant >: IT-01 FAIL vì 409 thay cho 201.", flush=True)
        run([executable, "-B", "-m", "scripts.debug_axis5", "409"], cwd=target, check=True, timeout=30)
        repository.write_text(original, encoding="utf-8")
        restored = check_case()
        assert restored.returncode == 0, restored.stderr
        print("Khôi phục >=: IT-01 PASS.")


if __name__ == "__main__":
    main()
