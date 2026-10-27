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
PYPROJECT = """\
[project]
name = "amt"
dependencies = [
    "rdflib>=7.0",
    "pyshacl>=0.25",   # SHACL
    "pyvis[extra]>=0.3",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "Pillow>=10.1", "PyYAML>=6.0"]
"""


def test_only_the_run_time_dependencies_are_installed(monkeypatch, tmp_path):
    repo = tmp_path / "engine"
    repo.mkdir()
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)
    (repo / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    # the development packages of the engine's requirements.txt are not wanted
    (repo / "requirements.txt").write_text("rdflib>=7.0\npytest>=7\nPillow>=10\nPyYAML>=6\n", encoding="utf-8")

    deps, source = run_amt._engine_dependencies()
    assert deps == ["rdflib>=7.0", "pyshacl>=0.25", "pyvis[extra]>=0.3"]
    assert "pyproject.toml" in source


def test_text_reader_gives_the_same_list_as_tomllib(monkeypatch):
    # Python 3.10 has no tomllib; the small reader must agree with it where it exists
    assert run_amt._dependencies_from_text(PYPROJECT) == ["rdflib>=7.0", "pyshacl>=0.25", "pyvis[extra]>=0.3"]
    assert run_amt._dependencies_from_text("[tool.x]\ndependencies = [\"z\"]\n") == []
    tomllib = pytest.importorskip("tomllib")
    assert tomllib.loads(PYPROJECT)["project"]["dependencies"] == run_amt._dependencies_from_text(PYPROJECT)


def test_fingerprint_follows_the_engines_dependencies(monkeypatch, tmp_path):
    repo = tmp_path / "engine"
    repo.mkdir()
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)

    fallback = hashlib.sha256("\n".join(run_amt.AMT_FALLBACK_DEPS).encode()).hexdigest()
    assert run_amt._engine_dependencies() == (run_amt.AMT_FALLBACK_DEPS, "built-in list")
    assert run_amt._deps_fingerprint() == fallback

    (repo / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    first = run_amt._deps_fingerprint()
    assert first != fallback

    # a change that is not a run-time dependency leaves the fingerprint alone ...
    (repo / "pyproject.toml").write_text(PYPROJECT.replace("pytest>=7.0", "pytest>=8.0"), encoding="utf-8")
    assert run_amt._deps_fingerprint() == first
    # ... a run-time dependency changes it
    (repo / "pyproject.toml").write_text(PYPROJECT.replace("rdflib>=7.0", "rdflib>=7.1"), encoding="utf-8")
    assert run_amt._deps_fingerprint() != first


def test_broken_pyproject_falls_back(monkeypatch, tmp_path):
    repo = tmp_path / "engine"
    repo.mkdir()
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)
    (repo / "pyproject.toml").write_text("this is [not toml", encoding="utf-8")
    assert run_amt._engine_dependencies()[1] == "built-in list"


def test_install_passes_exactly_the_run_time_dependencies_to_pip(monkeypatch, tmp_path, capsys):
    repo = tmp_path / "engine"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    monkeypatch.setattr(run_amt, "REPO_DIR", repo)
    monkeypatch.setattr(run_amt, "DEPS_MARKER", tmp_path / ".deps-installed")
    called = []
    monkeypatch.setattr(run_amt, "run", lambda cmd, **kw: called.append([str(c) for c in cmd]))
    run_amt.ensure_deps()
    assert called == [[sys.executable, "-m", "pip", "install", "--quiet", "rdflib>=7.0", "pyshacl>=0.25", "pyvis[extra]>=0.3"]]
    assert (tmp_path / ".deps-installed").read_text() == run_amt._deps_fingerprint()
    assert "pyproject.toml" in capsys.readouterr().out


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


# --------------------------------------------------------------------------- #
# Hint after a run
# --------------------------------------------------------------------------- #
def test_run_ends_with_a_hint_to_the_explorer(monkeypatch, tmp_path, capsys):
    outdir = tmp_path / "out"
    inp = tmp_path / "animals.ttl"
    inp.write_text("# x\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):                       # stands in for `python -m amt.runner`
        run_dir = Path(cmd[cmd.index("-o") + 1])
        (run_dir / "animals.reasoned.ttl").write_text("# x\n", encoding="utf-8")

    monkeypatch.setattr(run_amt, "run", fake_run)
    run_amt.run_pipeline(inp, outdir, [])
    out = capsys.readouterr().out
    assert run_amt.EXPLORER_URL in out and "animals.reasoned.ttl" in out


def test_no_hint_when_there_is_no_reasoned_file(monkeypatch, tmp_path, capsys):
    inp = tmp_path / "animals.ttl"
    inp.write_text("# x\n", encoding="utf-8")
    monkeypatch.setattr(run_amt, "run", lambda cmd, **kw: None)
    run_amt.run_pipeline(inp, tmp_path / "out", [])
    assert run_amt.EXPLORER_URL not in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# Checking without writing; explaining failures
# --------------------------------------------------------------------------- #
def test_check_only_is_a_wrapper_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_amt.py", "in.ttl", "--check-only", "--strict"])
    args, passthrough = run_amt.parse_args()
    assert args.check_only is True
    assert passthrough == ["--strict"]


def test_check_only_makes_no_run_folder(monkeypatch, tmp_path):
    inp = tmp_path / "x.ttl"
    inp.write_text("# x\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(run_amt, "run", lambda cmd, **kw: calls.append([str(c) for c in cmd]))
    run_amt.run_pipeline(inp, tmp_path / "out", [], check_only=True)
    assert not (tmp_path / "out").exists()
    assert "--check-only" in calls[0] and "-o" not in calls[0]


def test_old_cached_engine_is_told_to_update(monkeypatch, tmp_path, capsys):
    inp = tmp_path / "x.ttl"
    inp.write_text("# x\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run_amt.py", str(inp), "--check-only"])
    monkeypatch.setattr(run_amt, "ensure_repo", lambda ref, update: None)
    monkeypatch.setattr(run_amt, "engine_supports", lambda flag: False)
    assert run_amt.main() == 2
    err = capsys.readouterr().err
    assert "--check-only" in err and "--update" in err


@pytest.mark.parametrize("code, words", [(1, "did not pass"), (3, "unexpected error"), (7, "--update")])
def test_failed_run_is_explained(monkeypatch, tmp_path, capsys, code, words):
    inp = tmp_path / "x.ttl"
    inp.write_text("# x\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run_amt.py", str(inp)])
    monkeypatch.setattr(run_amt, "ensure_repo", lambda ref, update: None)
    monkeypatch.setattr(run_amt, "ensure_deps", lambda: None)

    def failing(*a, **k):
        raise subprocess.CalledProcessError(code, "x")

    monkeypatch.setattr(run_amt, "run_pipeline", failing)
    assert run_amt.main() == code
    err = capsys.readouterr().err
    assert words in err and run_amt.HOWTO_URL in err
