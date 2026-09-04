#!/usr/bin/env python3
"""check_migration_log: a spec change must bump VERSION and log a migration.

`spec/MIGRATIONS.md` states the rule: every change to
`spec/trace-event.schema.json` or `spec/event-types.yaml` MUST add a row
there, and `spec/event-types.yaml` says the same change MUST bump the
version. AGENTS.md named this gate as the load-bearing one in June 2026.
Nothing enforced it until now; this script does.

Checks, in order:

  1. `spec/VERSION` and the `version:` key in `spec/event-types.yaml`
     agree. This runs unconditionally; it needs no git history.
  2. `spec/MIGRATIONS.md` carries a row whose first cell is the current
     `spec/VERSION`. Also unconditional.
  3. If either governed file differs from the base ref, then
     `spec/VERSION` must also differ from the base ref. A schema or
     vocabulary change that ships under the old version fails here.

The base ref is resolved as: `$MIGRATION_BASE_REF` if set; otherwise
`origin/main` when it exists and is not the current commit (the pull
request case); otherwise `HEAD~1` (the push-to-main case). Locally, the
working tree is always the "after" side, so an uncommitted spec edit
without a bump fails before it is committed.

Exit codes: 0 OK, 1 violations found, 2 could not determine a base ref.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"
VERSION_FILE = SPEC / "VERSION"
EVENT_TYPES = SPEC / "event-types.yaml"
SCHEMA = SPEC / "trace-event.schema.json"
MIGRATIONS = SPEC / "MIGRATIONS.md"

GOVERNED = ("spec/trace-event.schema.json", "spec/event-types.yaml")
VERSION_RE = re.compile(r"^\s*version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+)[\"']?\s*$", re.M)
ROW_RE = re.compile(r"^\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|", re.M)


def git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def resolve_base_ref() -> str | None:
    override = os.environ.get("MIGRATION_BASE_REF")
    if override:
        return override if git("rev-parse", "--verify", override) else None
    head = git("rev-parse", "HEAD")
    main = git("rev-parse", "--verify", "origin/main")
    if main and head and main != head:
        base = git("merge-base", "origin/main", "HEAD")
        return base or "origin/main"
    if git("rev-parse", "--verify", "HEAD~1"):
        return "HEAD~1"
    return None


def read_at(ref: str, rel: str) -> str | None:
    """Read a single-line value (spec/VERSION) at a ref. Whitespace-stripped."""
    return git("show", f"{ref}:{rel}")


def main() -> int:
    violations: list[str] = []

    if not VERSION_FILE.is_file():
        print(f"check_migration_log FAILED: {VERSION_FILE.relative_to(ROOT)} missing")
        return 1
    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    # 1. VERSION and event-types.yaml agree.
    et_text = EVENT_TYPES.read_text(encoding="utf-8") if EVENT_TYPES.is_file() else ""
    et_match = VERSION_RE.search(et_text)
    et_version = et_match.group(1) if et_match else None
    if et_version != version:
        violations.append(
            f"spec/event-types.yaml declares version {et_version!r}; spec/VERSION is {version!r}"
        )

    # 2. MIGRATIONS.md has a row for the current version.
    mig_text = MIGRATIONS.read_text(encoding="utf-8") if MIGRATIONS.is_file() else ""
    logged = set(ROW_RE.findall(mig_text))
    if version not in logged:
        violations.append(
            f"spec/MIGRATIONS.md has no row for version {version}; "
            f"add one (rows found: {', '.join(sorted(logged)) or 'none'})"
        )

    # 3. Governed change implies a version bump.
    base = resolve_base_ref()
    if base is None:
        print(
            "check_migration_log: could not resolve a base ref (no origin/main, "
            "no HEAD~1, no MIGRATION_BASE_REF); skipped the diff check"
        )
        if violations:
            print(f"check_migration_log FAILED ({len(violations)} violation(s)):")
            for line in violations:
                print(f"  - {line}")
            return 1
        return 2

    # Let git decide what changed: it handles autocrlf, trailing newlines, and
    # base-to-working-tree comparison correctly, which a byte compare does not.
    diff = git("diff", "--name-only", base, "--", *GOVERNED)
    changed = [line.strip() for line in (diff or "").splitlines() if line.strip()]
    if changed:
        base_version = (read_at(base, "spec/VERSION") or "").strip()
        if base_version == version:
            violations.append(
                f"{', '.join(changed)} changed against {base} but spec/VERSION "
                f"is still {version}; bump it and add a spec/MIGRATIONS.md row"
            )

    if violations:
        print(f"check_migration_log FAILED ({len(violations)} violation(s)):")
        for line in violations:
            print(f"  - {line}")
        return 1

    state = f"{len(changed)} governed file(s) changed vs {base}" if changed else f"no governed change vs {base}"
    print(f"check_migration_log OK (version {version} logged; {state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
