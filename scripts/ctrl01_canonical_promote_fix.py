from __future__ import annotations

import subprocess
from pathlib import Path

import ctrl01_canonical_promote as m

FIX_PATH = "scripts/ctrl01_canonical_promote_fix.py"
m.TEMP_ALLOWED.add(FIX_PATH)

_original_restore = m.restore_transport


def restore_transport(repo: Path) -> None:
    _original_restore(repo)
    fix = repo / FIX_PATH
    if fix.exists():
        fix.unlink()


m.restore_transport = restore_transport


def commit_and_push(trigger: str) -> str:
    m.run("git", "config", "user.name", "epd2-governance-bot")
    m.run("git", "config", "user.email", "epd2-governance-bot@users.noreply.github.com")
    m.run("git", "add", "-A")
    if subprocess.run(("git", "diff", "--cached", "--quiet")).returncode == 0:
        m.fail("no canonical governance delta")

    # The final index must restore the borrowed PILOT guard exactly to the
    # accepted baseline and must contain none of the temporary transport files.
    if subprocess.run(
        (
            "git",
            "diff",
            "--cached",
            "--quiet",
            m.BASE_MAIN,
            "--",
            ".github/workflows/pilot-roadmap-guard.yml",
        )
    ).returncode != 0:
        m.fail("final PILOT guard does not match accepted baseline bytes")

    for rel in (
        ".github/workflows/ctrl01-c1-promote-canonical.yml",
        "scripts/ctrl01_canonical_promote.py",
        FIX_PATH,
    ):
        if m.run("git", "ls-files", "--stage", "--", rel, capture=True):
            m.fail(f"temporary transport path remains in final index: {rel}")

    staged = m.run("git", "diff", "--cached", "--name-only", capture=True).splitlines()
    if "services/control-plane-service/pyproject.toml" not in staged:
        m.fail("control-plane-service is not staged for canonical installation")
    if "docs/ctrl/CTRL-01/CTRL01_C1_ACCEPTANCE_RECORD.json" not in staged:
        m.fail("acceptance record not staged")
    if "docs/ctrl/CTRL-01/CTRL01_C1_CANONICAL_INSTALLATION_MANIFEST.json" not in staged:
        m.fail("canonical installation manifest not staged")
    if "docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md" not in staged:
        m.fail("PCR transition not staged")

    m.run("git", "commit", "-m", "governance(ctrl01): accept and install bounded CTRL-01 C1")
    m.run("git", "fetch", "origin", "main")
    origin = m.run("git", "rev-parse", "origin/main", capture=True)
    if origin != trigger:
        m.fail(f"canonical main moved before push: {origin} != {trigger}")
    m.run("git", "push", "origin", "HEAD:main")
    return m.run("git", "rev-parse", "HEAD", capture=True)


m.commit_and_push = commit_and_push
m.main()
