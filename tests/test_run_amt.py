"""
Offline tests for run_amt.py.

The engine is replaced by a small local git repository, so nothing here
touches the network. What is tested is the part of the wrapper that has
broken before: resolving a ref in the cached, shallow clone (0.2.0 fixed a
stale local branch and tags that were missing from the shallow history), the
dependency fingerprint, and how arguments are split between the wrapper and
the engine.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import run_amt

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH")

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.org",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.org",
}


def git(*args: str, cwd: Path) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        env={**os.environ, **GIT_ENV},
    )
    return out.stdout.strip()


def commit(repo: Path, name: str, text: str, message: str) -> str:
    (repo / name).write_text(text, encoding="utf-8")
    git("add", name, cwd=repo)
    git("commit", "-q", "-m", message, cwd=repo)
    return git("rev-parse", "HEAD", cwd=repo)


@pytest.fixture
def origin(tmp_path: Path) -> dict:
    """A local stand-in for amt-engine: tag v1 on the first commit, an untagged
    commit in between, and main one further ahead."""
    repo = tmp_path / "origin"
    repo.mkdir()
    git("init", "-q", cwd=repo)
    git("checkout", "-q", "-b", "main", cwd=repo)
    first = commit(repo, "README.md", "one\n", "first")
    git("tag", "v1", cwd=repo)
    mid = commit(repo, "MID.md", "mid\n", "second")  # reachable only through history
    tip = commit(repo, "requirements.txt", "rdflib>=7.0\n", "third")
    return {"path": repo, "first": first, "mid": mid, "tip": tip}


@pytest.fixture
def cache(tmp_path: Path, origin: dict, monkeypatch) -> Path:
    """Point run_amt at the local origin and a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(run_amt, "AMT_REPO_URL", origin["path"].as_uri())
    monkeypatch.setattr(run_amt, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(run_amt, "REPO_DIR", cache_dir / "amt-engine")
    monkeypatch.setattr(run_amt, "DEPS_MARKER", cache_dir / ".deps-installed")
    return cache_dir / "amt-engine"


def head(repo: Path) -> str:
    return git("rev-parse", "HEAD", cwd=repo)


# --------------------------------------------------------------------------- #
# Version
# --------------------------------------------------------------------------- #
def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", run_amt.__version__)


# --------------------------------------------------------------------------- #
# Cloning and ref resolution
# --------------------------------------------------------------------------- #
def test_clone_checks_out_tip_detached(cache: Path, origin: dict):
    run_amt.ensure_repo("main", update=False)
    assert head(cache) == origin["tip"]
    assert (cache / "requirements.txt").exists()
    # detached: no local branch that could go stale
    assert subprocess.run(
        ["git", "-C", str(cache), "symbolic-ref", "-q", "HEAD"], capture_output=True
    ).returncode != 0


def test_tag_missing_from_shallow_clone_is_fetched_on_demand(cache: Path, origin: dict):
    run_amt.ensure_repo("main", update=False)
    assert head(cache) == origin["tip"]  # depth-1 clone: v1 is not in it yet
    run_amt.ensure_repo("v1", update=False)
    assert head(cache) == origin["first"]
    assert not (cache / "requirements.txt").exists()  # only in the second commit


def test_commit_sha_outside_shallow_history_is_resolved(cache: Path, origin: dict):
    run_amt.ensure_repo("main", update=False)
    run_amt.ensure_repo(origin["mid"], update=False)  # no branch or tag points here
    assert head(cache) == origin["mid"]


def test_update_follows_the_remote_tip(cache: Path, origin: dict):
    run_amt.ensure_repo("main", update=False)
    new_tip = commit(origin["path"], "NEWS.md", "news\n", "third")
    # without --update the cache keeps the old engine, by design
    run_amt.ensure_repo("main", update=False)
    assert head(cache) == origin["tip"]
    run_amt.ensure_repo("main", update=True)
    assert head(cache) == new_tip


def test_unknown_ref_exits_with_a_message(cache: Path, origin: dict):
    run_amt.ensure_repo("main", update=False)
    with pytest.raises(SystemExit) as err:
        run_amt._checkout("no-such-ref")
    assert "no-such-ref" in str(err.value)


# --------------------------------------------------------------------------- #
# Dependencies
# --------------------------------------------------------------------------- #
def test_fingerprint_follows_the_engines_requirements(cache: Path, monkeypatch, tmp_path):
    repo = tmp_path / "engine"
    repo.mkdir()
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)

    fallback = hashlib.sha256("\n".join(run_amt.AMT_FALLBACK_DEPS).encode()).hexdigest()
    assert run_amt._requirements_file() is None
    assert run_amt._deps_fingerprint() == fallback

    req = repo / "requirements.txt"
    req.write_bytes(b"rdflib>=7.0\n")
    first = run_amt._deps_fingerprint()
    assert first == hashlib.sha256(b"rdflib>=7.0\n").hexdigest() != fallback

    req.write_bytes(b"rdflib>=7.0\npyshacl>=0.25\n")
    assert run_amt._deps_fingerprint() != first


# --------------------------------------------------------------------------- #
# Feature detection
# --------------------------------------------------------------------------- #
def test_engine_supports_reads_the_engines_runner(monkeypatch, tmp_path):
    repo = tmp_path / "engine"
    (repo / "amt").mkdir(parents=True)
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)

    # runner.py absent: cannot tell, so let the engine reject the flag itself
    assert run_amt.engine_supports("--minimal") is True

    (repo / "amt" / "runner.py").write_text('p.add_argument("--no-check")\n', encoding="utf-8")
    assert run_amt.engine_supports("--minimal") is False

    (repo / "amt" / "runner.py").write_text('p.add_argument("--minimal")\n', encoding="utf-8")
    assert run_amt.engine_supports("--minimal") is True


# --------------------------------------------------------------------------- #
# Arguments
# --------------------------------------------------------------------------- #
def test_unknown_flags_pass_through_to_the_engine(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["run_amt.py", "in.ttl", "--minimal", "--no-check", "--height", "900px"],
    )
    args, passthrough = run_amt.parse_args()
    assert args.input == Path("in.ttl")
    assert args.minimal is True
    assert passthrough == ["--no-check", "--height", "900px"]


def test_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_amt.py", "in.ttl"])
    args, passthrough = run_amt.parse_args()
    assert args.ref == "main"
    assert args.outdir == Path("out")
    assert args.minimal is False and args.update is False
    assert passthrough == []


# --------------------------------------------------------------------------- #
# Output folder
# --------------------------------------------------------------------------- #
def test_latest_pointer_follows_the_newest_run(tmp_path):
    outdir = tmp_path / "out"
    first = outdir / "run-1"
    second = outdir / "run-2"
    for run_dir, text in ((first, "one"), (second, "two")):
        run_dir.mkdir(parents=True)
        (run_dir / "x.txt").write_text(text, encoding="utf-8")

    run_amt._update_latest_pointer(outdir, first)
    assert (outdir / "latest" / "x.txt").read_text(encoding="utf-8") == "one"

    run_amt._update_latest_pointer(outdir, second)
    assert (outdir / "latest" / "x.txt").read_text(encoding="utf-8") == "two"
