"""v1.9.4 shipped ten megabytes of the previous brand's executable inside
every download. Releases are packaged locally, because no signing provider is
configured for hosted builds, and the packaging step archives whatever sits in
dist/ - including a binary built weeks earlier under the old name. The
signature gate missed it because that leftover was validly signed too."""

import os
import check_release


def _dist(tmp_path, *names):
    directory = tmp_path / "dist" / "Redexa Social"
    directory.mkdir(parents=True)
    for name in names:
        (directory / name).write_bytes(b"MZ")
    return directory


def test_an_executable_the_build_does_not_produce_stops_the_release(tmp_path, monkeypatch):
    directory = _dist(tmp_path, "Redexa Social.exe", "updater.exe", "Social Dashboard.exe")
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(directory, "Redexa Social.exe"))
    problems = check_release.check_dist_contents()
    assert len(problems) == 1
    assert "Social Dashboard.exe" in problems[0]


def test_the_expected_build_output_passes(tmp_path, monkeypatch):
    directory = _dist(tmp_path, "Redexa Social.exe", "updater.exe")
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(directory, "Redexa Social.exe"))
    assert check_release.check_dist_contents() == []


def test_a_missing_dist_directory_is_not_this_check_s_problem(tmp_path, monkeypatch):
    monkeypatch.setattr(check_release, "DIST_EXE", os.path.join(tmp_path, "nope", "Redexa Social.exe"))
    assert check_release.check_dist_contents() == []
