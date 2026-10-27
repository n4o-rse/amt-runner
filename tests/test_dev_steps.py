"""Offline tests for the helpers behind the network steps ``drift`` and ``smoke``.

The steps themselves need the network and are started by hand or by the weekly
workflow; the decisions they make are plain functions and are covered here.
"""
from pathlib import Path

from step_drift import INTENDED, compare
from step_smoke import EXPECTED_FILES, command, inferred_edges, missing_files, newest_run


def write(directory: Path, name: str, text: str, newline: str = "\n") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(text.replace("\n", newline).encode("utf-8"))


def test_identical_files_are_the_same_even_with_crlf(tmp_path: Path):
    write(tmp_path / "here", "a.ttl", "one\ntwo\n", newline="\r\n")
    write(tmp_path / "engine", "a.ttl", "one\ntwo\n")
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["same"] == ["a.ttl"]
    assert found["different"] == []


def test_changed_content_is_drift(tmp_path: Path):
    write(tmp_path / "here", "a.ttl", "old\n")
    write(tmp_path / "engine", "a.ttl", "new\n")
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["different"] == ["a.ttl"]
    assert found["same"] == []


def test_intended_difference_is_not_drift(tmp_path: Path):
    name = next(iter(INTENDED))
    stem = name.rsplit(".", 1)[0]
    write(tmp_path / "here", stem + ".ttl", "x\n")
    write(tmp_path / "engine", stem + ".ttl", "x\n")
    write(tmp_path / "here", name, "python run_amt.py\n")
    write(tmp_path / "engine", name, "python -m amt.runner\n")
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["intended"] == [name]
    assert found["different"] == []


def test_file_gone_from_the_engine_is_reported(tmp_path: Path):
    write(tmp_path / "here", "a.ttl", "x\n")
    (tmp_path / "engine").mkdir()
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["missing"] == ["a.ttl"]


def test_engine_only_files_are_listed_but_do_not_count(tmp_path: Path):
    write(tmp_path / "here", "a.ttl", "x\n")
    write(tmp_path / "engine", "a.ttl", "x\n")
    write(tmp_path / "engine", "extra.ttl", "y\n")
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["engine_only"] == ["extra.ttl"]
    assert found["different"] == [] and found["missing"] == []


def test_files_without_a_ttl_partner_are_not_compared(tmp_path: Path):
    # README.md-like files in the repository root must never be looked up
    write(tmp_path / "here", "README.md", "readme\n")
    write(tmp_path / "here", "a.ttl", "x\n")
    write(tmp_path / "engine", "a.ttl", "x\n")
    found = compare(tmp_path / "here", tmp_path / "engine")
    assert found["same"] == ["a.ttl"]
    assert found["missing"] == []


def test_inferred_edges_are_read_from_the_output():
    out = "LOAD ...\n          reasoning produced 106 inferred edge(s)\nOK ..."
    assert inferred_edges(out) == 106
    assert inferred_edges("nothing here") is None


def test_missing_output_files_are_named(tmp_path: Path):
    for name in EXPECTED_FILES[:-1]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert missing_files(tmp_path) == [EXPECTED_FILES[-1]]


def test_newest_run_is_the_last_by_name(tmp_path: Path):
    for name in ("run-20260101-000000", "run-20260301-000000", "run-20260201-000000"):
        (tmp_path / name).mkdir()
    (tmp_path / "latest").mkdir()
    assert newest_run(tmp_path).name == "run-20260301-000000"
    assert newest_run(tmp_path / "nowhere") is None


def test_smoke_always_updates_the_cached_engine():
    # a stale .amt-cache once let the smoke test pass against an engine from before the change under test
    assert "--update" in command() and "animals.ttl" in command()
