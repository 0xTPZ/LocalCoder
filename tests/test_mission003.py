from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from localcoder.audit import AuditEvent, AuditStore
from localcoder.checkpoints import CheckpointStore
from localcoder.mission_engine.journal import JournalStore
from localcoder.persistence import AtomicJsonStore, FileLock, LockConflictError
from localcoder.recovery import RecoveryManager, RecoveryStatus
from localcoder.schemas import SchemaRegistry
from localcoder.state import CheckpointRecord, format_utc


ROOT = Path(__file__).parents[1]


class Mission003Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="localcoder-m003-")
        self.root = Path(self.tempdir.name)
        self.registry = SchemaRegistry(ROOT / "schemas")
        self.checkpoints = CheckpointStore(self.root / "checkpoints", self.registry)
        self.journal = JournalStore(self.root / "journal.jsonl", self.registry)
        self.audit = AuditStore(self.root / "audit.jsonl", self.registry)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def timestamp(self, seconds: int = 0) -> datetime:
        return datetime(2026, 10, 3, 12, 0, seconds, tzinfo=timezone.utc)

    def checkpoint(self, checkpoint_id: str = "checkpoint-1", state: str = "PAUSED") -> CheckpointRecord:
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            project_id="project-1",
            roadmap_id="roadmap-1",
            mission_id="mission-1",
            task_id="task-1",
            action_id="action-1",
            created_at=self.timestamp(),
            lifecycle_state=state,
            completed_steps=("plan",),
            in_progress_step="verify",
            pause_reason="operator pause",
            next_action="verify",
            backend_id=None,
            model_id=None,
            active_capabilities=(),
            operation_id="operation-1",
        )

    def env(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        return environment

    def run_helper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "tests" / "crash_helpers.py"), *args],
            cwd=ROOT,
            env=self.env(),
            text=True,
            capture_output=True,
            timeout=15,
        )

    def test_checkpoint_store_create_read_replace_enumerate_and_active(self) -> None:
        original = self.checkpoint()
        self.checkpoints.create(original)
        self.assertEqual(self.checkpoints.get(original.checkpoint_id), original)
        self.assertEqual(self.checkpoints.active("project-1").checkpoint_id, original.checkpoint_id)
        replacement = self.checkpoint(state="RESUMABLE")
        self.checkpoints.replace(replacement)
        self.assertEqual(self.checkpoints.enumerate("project-1"), (replacement,))
        with self.assertRaises(RuntimeError):
            self.checkpoints.create(replacement)

    def test_checkpoint_invalid_replace_preserves_last_valid_state(self) -> None:
        original = self.checkpoint()
        self.checkpoints.create(original)
        path = self.root / "checkpoints" / "checkpoint-1.json"
        invalid = dict(original.to_document())
        invalid["lifecycle_state"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            AtomicJsonStore(path, "checkpoint", self.registry).save(invalid)
        self.assertEqual(self.checkpoints.get("checkpoint-1"), original)

    def test_audit_store_appends_orders_deduplicates_and_redacts(self) -> None:
        protected_fixture = "fixture-audit-secret"
        event = AuditEvent("ACTION_STARTED", "test", "action-1", action_id="action-1", correlation_id="corr-1", data={"password": protected_fixture})
        first = self.audit.append(event)
        duplicate = self.audit.append(event)
        self.assertEqual(first, duplicate)
        self.assertEqual(first["sequence"], 1)
        self.assertNotIn(protected_fixture, self.audit.path.read_text(encoding="utf-8"))
        self.assertEqual(len(self.audit.read().events), 1)

    def test_audit_store_ignores_only_truncated_final_record(self) -> None:
        self.audit.append(AuditEvent("ACTION_STARTED", "test", "action-1"))
        with self.audit.path.open("ab") as stream:
            stream.write(b'{"schema_version":1,"event_id":"partial"')
        report = self.audit.read()
        self.assertTrue(report.ignored_final_record)
        self.assertEqual(len(report.events), 1)

    def test_journal_classifies_started_without_terminal(self) -> None:
        self.journal.planned("operation-1", "action-1")
        self.journal.started("operation-1", "action-1")
        self.assertEqual(self.journal.interrupted_operations(), ("operation-1",))
        self.journal.completed("operation-1", "action-1")
        self.assertEqual(self.journal.interrupted_operations(), ())

    def test_journal_ignores_truncated_tail_and_preserves_valid_entries(self) -> None:
        self.journal.planned("operation-1", "action-1")
        with self.journal.path.open("ab") as stream:
            stream.write(b'{"schema_version":1,"journal_id":"partial"')
        report = self.journal.read()
        self.assertTrue(report.ignored_final_record)
        self.assertEqual(len(report.entries), 1)

    def test_recovery_clean_after_completed_operation(self) -> None:
        self.journal.planned("operation-1", "action-1")
        self.journal.started("operation-1", "action-1")
        self.journal.completed("operation-1", "action-1")
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(report.status, RecoveryStatus.CLEAN)
        self.assertFalse(report.safe_to_resume)

    def test_recovery_ambiguous_does_not_authorize_automatic_repeat(self) -> None:
        self.journal.planned("operation-1", "action-1")
        self.journal.started("operation-1", "action-1")
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(report.status, RecoveryStatus.AMBIGUOUS)
        self.assertFalse(report.safe_to_resume)
        self.assertEqual(report.recommendation, "STOP_AND_REQUEST_HUMAN_DECISION")

    def test_recovery_recognizes_valid_active_checkpoint(self) -> None:
        self.checkpoints.create(self.checkpoint())
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect("project-1")
        self.assertEqual(report.status, RecoveryStatus.RECOVERABLE)
        self.assertTrue(report.safe_to_resume)
        self.assertEqual(report.active_checkpoint_ids, ("checkpoint-1",))

    def test_recovery_blocks_when_state_lock_is_live(self) -> None:
        lock = FileLock(self.checkpoints.lock_path, "test-live-lock")
        lock.acquire()
        try:
            report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        finally:
            lock.release()
        self.assertEqual(report.status, RecoveryStatus.BLOCKED)
        self.assertFalse(report.safe_to_resume)

    def test_multiple_active_checkpoints_are_ambiguous(self) -> None:
        self.checkpoints.create(self.checkpoint("checkpoint-1"))
        self.checkpoints.create(self.checkpoint("checkpoint-2"))
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect("project-1")
        self.assertEqual(report.status, RecoveryStatus.AMBIGUOUS)
        self.assertFalse(report.safe_to_resume)

    def test_recovery_classifies_corrupt_and_unknown_checkpoint(self) -> None:
        corrupt = self.root / "checkpoints" / "corrupt.json"
        corrupt.parent.mkdir(parents=True, exist_ok=True)
        corrupt.write_text('{"schema_version": 1', encoding="utf-8")
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(report.status, RecoveryStatus.CORRUPTED)

        corrupt.unlink()
        unknown = self.root / "checkpoints" / "unknown.json"
        unknown.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(report.status, RecoveryStatus.CORRUPTED)

    def test_recovery_reports_abandoned_checkpoint_temporary_without_promoting(self) -> None:
        self.checkpoints.create(self.checkpoint())
        temporary = self.root / "checkpoints" / ".checkpoint-1.json.crashed.tmp"
        temporary.write_text(json.dumps(self.checkpoint(state="RESUMABLE").to_document()), encoding="utf-8")
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect("project-1")
        self.assertEqual(report.status, RecoveryStatus.RECOVERABLE)
        self.assertEqual(len(report.abandoned_temporary_files), 1)
        self.assertEqual(self.checkpoints.get("checkpoint-1").lifecycle_state, "PAUSED")

    def test_real_subprocess_dies_during_atomic_write_and_main_survives(self) -> None:
        path = self.root / "project.json"
        original = {
            "schema_version": 1,
            "project_id": "crash-project",
            "root_path": "E:\\crash-project",
            "roadmap_id": None,
            "created_at": "2026-10-03T12:00:00.000Z",
            "status": "ACTIVE",
            "metadata": {},
        }
        store = AtomicJsonStore(path, "project", self.registry)
        store.save(original)
        result = self.run_helper("atomic-crash", str(path))
        self.assertEqual(result.returncode, 71, result.stderr)
        self.assertEqual(store.load(), original)
        self.assertTrue(store.temporary_paths())

    def test_real_subprocess_dies_before_write_and_no_false_operation_exists(self) -> None:
        result = self.run_helper("die-before-write")
        self.assertEqual(result.returncode, 72)
        self.assertFalse(self.journal.path.exists())
        report = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(report.status, RecoveryStatus.CLEAN)

    def test_two_processes_cannot_acquire_same_lock_and_stale_is_explicit(self) -> None:
        path = self.root / "shared.lock"
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "crash_helpers.py"), "hold-lock", str(path)],
            cwd=ROOT,
            env=self.env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            lock_id = process.stdout.readline().strip() if process.stdout else ""
            self.assertTrue(lock_id)
            with self.assertRaises(LockConflictError):
                FileLock(path, "second-instance").acquire()
        finally:
            process.terminate()
            process.wait(timeout=10)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
        info = FileLock.inspect(path)
        self.assertIsNotNone(info)
        self.assertTrue(FileLock.is_stale(info))
        FileLock.release_stale(path, lock_id)
        lock = FileLock(path, "after-stale")
        lock.acquire()
        lock.release()

    def test_restart_after_completed_operation_is_not_ambiguous(self) -> None:
        self.journal.planned("operation-2", "action-2")
        self.journal.started("operation-2", "action-2")
        self.journal.completed("operation-2", "action-2")
        restarted = RecoveryManager(self.checkpoints, self.journal, self.audit).inspect()
        self.assertEqual(restarted.ambiguous_operation_ids, ())
        self.assertEqual(restarted.status, RecoveryStatus.CLEAN)


if __name__ == "__main__":
    unittest.main()
