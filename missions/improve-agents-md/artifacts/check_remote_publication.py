#!/usr/bin/env python3
"""Check remote publication state without modifying refs in the shared checkout."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRANCH = "codex/improve-agents-md"
REPOSITORY = "ivdevV/Odoo16iRG"


class PublicationCheckError(RuntimeError):
    """Raised when current remote publication state cannot be inspected safely."""


def run(command: list[str], cwd: Path, *, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a command with captured output and optional reproducibility logging."""
    if verbose:
        print(f"$ {shlex.join(command)}")
    result = subprocess.run(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    if verbose and result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if verbose:
        print(f"[exit {result.returncode}]")
    return result


def required(command: list[str], cwd: Path, *, verbose: bool = False) -> str:
    result = run(command, cwd, verbose=verbose)
    if result.returncode:
        raise PublicationCheckError(f"required command failed: {shlex.join(command)}")
    return result.stdout


def inspect_remote_publication(
    root: Path,
    origin_url: str,
    *,
    temporary_parent: Path | None = None,
    snapshot_origin_url: str | None = None,
    verbose: bool = False,
) -> dict[str, object]:
    """Inspect remote ancestry in an ephemeral bare repo, cleaned on every exit."""
    remote_output = required(
        ["git", "ls-remote", origin_url, "refs/heads/*", "refs/pull/*/head"],
        root, verbose=verbose,
    )
    remote_entries = [line.split("\t", 1) for line in remote_output.splitlines() if line]
    if not remote_entries:
        raise PublicationCheckError("origin returned no branch or PR-head refs")

    with tempfile.TemporaryDirectory(
        prefix="improve-agents-publication-", dir=temporary_parent
    ) as snapshot_name:
        snapshot = Path(snapshot_name)
        required(["git", "init", "--bare", str(snapshot)], root, verbose=verbose)
        required(
            ["git", "--git-dir", str(snapshot), "fetch", "--no-tags",
             "--no-write-fetch-head", str(root), "+HEAD:refs/local/head"],
            root, verbose=verbose,
        )

        destinations: dict[str, str] = {}
        refspecs: list[str] = []
        base_ref: str | None = None
        for index, (_sha, source_ref) in enumerate(remote_entries, start=1):
            destination = f"refs/snapshot/{index:04d}"
            destinations[destination] = source_ref
            refspecs.append(f"+{source_ref}:{destination}")
            if source_ref == "refs/heads/Dev_iRG":
                base_ref = destination
        if base_ref is None:
            raise PublicationCheckError("origin has no refs/heads/Dev_iRG")

        required(
            ["git", "--git-dir", str(snapshot), "fetch", "--no-tags",
             "--no-write-fetch-head", snapshot_origin_url or origin_url, *refspecs],
            root, verbose=verbose,
        )
        base = required(
            ["git", "--git-dir", str(snapshot), "rev-parse", base_ref],
            root, verbose=verbose,
        ).strip()
        head = required(
            ["git", "--git-dir", str(snapshot), "rev-parse", "refs/local/head"],
            root, verbose=verbose,
        ).strip()
        unique_output = required(
            ["git", "--git-dir", str(snapshot), "rev-list", "--reverse",
             f"{base_ref}..refs/local/head"],
            root, verbose=verbose,
        )
        unique_commits = [line for line in unique_output.splitlines() if line]

        contained: list[dict[str, str]] = []
        for commit in unique_commits:
            for local_ref, remote_ref in destinations.items():
                result = run(
                    ["git", "--git-dir", str(snapshot), "merge-base",
                     "--is-ancestor", commit, local_ref],
                    root,
                )
                if result.returncode == 0:
                    contained.append({
                        "commit": commit,
                        "snapshot_ref": local_ref,
                        "remote_ref": remote_ref,
                    })
                elif result.returncode != 1:
                    raise PublicationCheckError(
                        f"merge-base returned {result.returncode} for {commit} in {local_ref}"
                    )

        return {
            "observed_base": base,
            "observed_head": head,
            "unique_commit_count": len(unique_commits),
            "fetched_remote_ref_count": len(remote_entries),
            "contained_unique_commits": contained,
        }


def main() -> int:
    try:
        origin_url = required(
            ["git", "remote", "get-url", "origin"], ROOT, verbose=True
        ).strip()
        summary = inspect_remote_publication(ROOT, origin_url, verbose=True)
    except PublicationCheckError as error:
        print(f"PUBLICATION CHECK FAILED: {error}")
        return 2

    gh_result = run(
        ["gh", "pr", "list", "--repo", REPOSITORY, "--state", "all",
         "--head", BRANCH, "--json", "number"],
        ROOT, verbose=True,
    )
    gh_status = "unavailable"
    gh_prs: list[object] | None = None
    if gh_result.returncode == 0:
        try:
            parsed = json.loads(gh_result.stdout)
            if not isinstance(parsed, list):
                raise ValueError("gh output is not a JSON list")
            gh_prs = parsed
            gh_status = "queried"
        except (json.JSONDecodeError, ValueError) as error:
            print(f"PUBLICATION CHECK FAILED: invalid gh JSON: {error}")
            return 2

    summary["gh_query_status"] = gh_status
    summary["gh_pull_requests"] = gh_prs
    print("CURRENT REMOTE STATE SUMMARY")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["contained_unique_commits"]:
        print("PUBLICATION CHECK FAILED: branch-unique commits are reachable remotely")
        return 1
    if gh_prs:
        print("PUBLICATION CHECK FAILED: gh reports a current matching PR")
        return 1

    print(
        "PUBLICATION CHECK PASS: current remote Git refs contain no branch-unique commit; "
        "inspection used an automatically cleaned ephemeral bare repository"
    )
    if gh_status == "unavailable":
        print(
            "CONCERN: the gh PR query was attempted but unavailable; "
            "no historical no-push/no-PR claim is made"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
