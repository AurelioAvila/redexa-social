"""The two release gates must agree on what a package contains.

check_release.py --dist refuses an executable the build is not supposed to
produce, and scripts/verify_release.py refuses a package missing one. An
earlier version of the first gate listed the expected names by hand and left
out "Social Dashboard.exe" - which looks like a leftover from the rename,
because the spec builds only "Redexa Social", but is a deliberate
compatibility launcher that release.yml copies in and verify_release.py
requires. Between them the two gates made every release impossible: one
failed if it was there, the other if it was not. Hence these tests."""

import os
import check_release
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from verify_release import REQUIRED_BINARIES


def _dist(tmp_path, *names):
    directory = tmp_path / "dist" / "Redexa Social"
    directory.mkdir(parents=True)
    for name in names:
        (directory / name).write_bytes(b"MZ")
    return directory


def test_the_two_gates_expect_the_same_executables():
    assert check_release._expected_binaries() == set(REQUIRED_BINARIES)


def test_the_compatibility_launcher_is_not_treated_as_a_leftover(tmp_path, monkeypatch):
    """Shortcuts made by installations under the old name point at it."""
    directory = _dist(tmp_path, *REQUIRED_BINARIES)
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(directory, "Redexa Social.exe"))
    assert check_release.check_dist_contents() == []


def test_an_executable_nothing_produces_stops_the_release(tmp_path, monkeypatch):
    directory = _dist(tmp_path, *REQUIRED_BINARIES, "Leftover Build.exe")
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(directory, "Redexa Social.exe"))
    problems = check_release.check_dist_contents()
    assert len(problems) == 1
    assert "Leftover Build.exe" in problems[0]


def test_a_missing_dist_directory_is_not_this_check_s_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(tmp_path, "nope", "Redexa Social.exe"))
    assert check_release.check_dist_contents() == []
