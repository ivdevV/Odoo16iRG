#!/usr/bin/env python3
"""Offline regression tests for remote-publication inspection isolation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_remote_publication import PublicationCheckError, inspect_remote_publication


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


class RemotePublicationIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.seed = self.root / "seed"
        self.origin = self.root / "origin.git"
        self.checkout = self.root / "checkout"
        self.snapshots = self.root / "snapshots"
        self.snapshots.mkdir()

        git(self.root, "init", "-b", "Dev_iRG", str(self.seed))
        git(self.seed, "config", "user.name", "Test")
        git(self.seed, "config", "user.email", "test@example.invalid")
        (self.seed / "base.txt").write_text("base\n", encoding="utf-8")
        git(self.seed, "add", "base.txt")
        git(self.seed, "commit", "-m", "base")
        git(self.root, "clone", "--bare", str(self.seed), str(self.origin))
        git(self.root, "clone", str(self.origin), str(self.checkout))
        git(self.checkout, "config", "user.name", "Test")
        git(self.checkout, "config", "user.email", "test@example.invalid")
        git(self.checkout, "switch", "-c", "codex/improve-agents-md")
        (self.checkout / "local.txt").write_text("local\n", encoding="utf-8")
        git(self.checkout, "add", "local.txt")
        git(self.checkout, "commit", "-m", "local")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_inspection_does_not_modify_shared_refs_and_cleans_snapshot(self) -> None:
        original_remote_ref = git(
            self.checkout, "rev-parse", "refs/remotes/origin/Dev_iRG"
        )
        (self.seed / "remote.txt").write_text("remote\n", encoding="utf-8")
        git(self.seed, "add", "remote.txt")
        git(self.seed, "commit", "-m", "remote advance")
        git(self.seed, "push", str(self.origin), "Dev_iRG")

        summary = inspect_remote_publication(
            self.checkout, str(self.origin), temporary_parent=self.snapshots
        )

        self.assertEqual(
            original_remote_ref,
            git(self.checkout, "rev-parse", "refs/remotes/origin/Dev_iRG"),
        )
        self.assertEqual([], list(self.snapshots.iterdir()))
        self.assertEqual(1, summary["unique_commit_count"])
        self.assertEqual([], summary["contained_unique_commits"])

    def test_snapshot_is_cleaned_when_remote_fetch_fails(self) -> None:
        with self.assertRaises(PublicationCheckError):
            inspect_remote_publication(
                self.checkout,
                str(self.root / "missing-origin.git"),
                temporary_parent=self.snapshots,
            )

        self.assertEqual([], list(self.snapshots.iterdir()))


if __name__ == "__main__":
    unittest.main()
