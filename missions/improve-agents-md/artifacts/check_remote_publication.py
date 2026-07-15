#!/usr/bin/env python3
"""Check current remote publication state for the improve-agents-md branch."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NAMESPACE = "refs/validation/improve-agents-md"
BRANCH = "codex/improve-agents-md"
REPOSITORY = "ivdevV/Odoo16iRG"


def run(
    command: list[str], input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root and print exact captured output."""
    print(f"$ {shlex.join(command)}")
    if input_text:
        print(input_text, end="" if input_text.endswith("\n") else "\n")
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    print(f"[exit {result.returncode}]")
    return result


def required(command: list[str], input_text: str | None = None) -> str:
    result = run(command, input_text=input_text)
    if result.returncode:
        raise RuntimeError(f"required command failed: {shlex.join(command)}")
    return result.stdout


def main() -> int:
    try:
        remote_output = required(
            ["git", "ls-remote", "origin", "refs/heads/*", "refs/pull/*/head"]
        )
        remote_entries = []
        for line in remote_output.splitlines():
            sha, source_ref = line.split("\t", 1)
            remote_entries.append((sha, source_ref))
        if not remote_entries:
            raise RuntimeError("origin returned no branch or PR-head refs")

        stale_output = required(
            ["git", "for-each-ref", "--format=%(refname)", NAMESPACE]
        )
        stale_refs = [line for line in stale_output.splitlines() if line]
        delete_input = "".join(f"delete {refname}\n" for refname in stale_refs)
        required(["git", "update-ref", "--stdin"], input_text=delete_input)

        destinations: dict[str, str] = {}
        refspecs = []
        for index, (_sha, source_ref) in enumerate(remote_entries, start=1):
            destination = f"{NAMESPACE}/snapshot/{index:04d}"
            destinations[destination] = source_ref
            refspecs.append(f"+{source_ref}:{destination}")
        required(
            [
                "git",
                "fetch",
                "--no-tags",
                "origin",
                *refspecs,
                "+refs/heads/Dev_iRG:refs/remotes/origin/Dev_iRG",
            ]
        )
        base = required(["git", "rev-parse", "origin/Dev_iRG"]).strip()
        head = required(["git", "rev-parse", "HEAD"]).strip()
        unique_output = required(
            ["git", "rev-list", "--reverse", "origin/Dev_iRG..HEAD"]
        )
        unique_commits = [line for line in unique_output.splitlines() if line]
        refs_output = required(
            [
                "git",
                "for-each-ref",
                "--format=%(refname)",
                f"{NAMESPACE}/snapshot",
            ]
        )
        remote_refs = [line for line in refs_output.splitlines() if line]
        if len(remote_refs) != len(remote_entries):
            raise RuntimeError(
                f"fetched {len(remote_refs)} of {len(remote_entries)} remote refs"
            )
    except RuntimeError as error:
        print(f"PUBLICATION CHECK FAILED: {error}")
        return 2

    contained: list[dict[str, str]] = []
    for commit in unique_commits:
        for refname in remote_refs:
            result = subprocess.run(
                ["git", "merge-base", "--is-ancestor", commit, refname],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.returncode == 0:
                contained.append(
                    {
                        "commit": commit,
                        "local_ref": refname,
                        "remote_ref": destinations[refname],
                    }
                )
            elif result.returncode != 1:
                print(
                    "PUBLICATION CHECK FAILED: merge-base returned "
                    f"{result.returncode} for {commit} in {refname}"
                )
                return 2

    gh_result = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            REPOSITORY,
            "--state",
            "all",
            "--head",
            BRANCH,
            "--json",
            "number",
        ]
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

    summary = {
        "observed_base": base,
        "observed_head": head,
        "unique_commit_count": len(unique_commits),
        "fetched_remote_ref_count": len(remote_refs),
        "contained_unique_commits": contained,
        "gh_query_status": gh_status,
        "gh_pull_requests": gh_prs,
    }
    print("CURRENT REMOTE STATE SUMMARY")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if contained:
        print(
            "PUBLICATION CHECK FAILED: branch-unique commits are currently "
            "reachable from fetched remote head/PR refs"
        )
        return 1
    if gh_prs:
        print("PUBLICATION CHECK FAILED: gh reports a current matching PR")
        return 1

    print(
        "PUBLICATION CHECK PASS: at observation time, no commit in "
        "origin/Dev_iRG..HEAD is reachable from any fetched remote branch head "
        "or refs/pull/*/head"
    )
    if gh_status == "unavailable":
        print(
            "CONCERN: the required gh PR query was attempted but unavailable; "
            "no historical no-push/no-PR claim is made"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
