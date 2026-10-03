from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from localcoder.audit import AuditEvent, MemoryAuditTrail
from localcoder.persistence import AtomicJsonStore
from localcoder.schemas import (
    SchemaRegistry,
    SchemaValidationError,
    StateCorruptionError,
    UnknownSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from localcoder.state import (
    CheckpointRecord,
    IdempotencyRegistry,
    OperationState,
    format_utc,
    parse_utc,
    redact,
    redact_text,
    stable_id,
    utc_now,
)


ROOT = Path(__file__).parents[1]


class Mission002Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SchemaRegistry(ROOT / "schemas")
        self.tempdir = tempfile.TemporaryDirectory(prefix="localcoder-m002-")
        self.temp = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def timestamp(self) -> str:
        return format_utc(datetime(2026, 10, 3, 12, 0, 0, 123456, tzinfo=timezone.utc))

    def documents(self) -> dict[str, dict]:
        timestamp = self.timestamp()
        return {
            "project": {"schema_version": 1, "project_id": "project-1", "root_path": "E:\\demo", "created_at": timestamp, "status": "ACTIVE"},
            "roadmap": {"schema_version": 1, "roadmap_id": "roadmap-1", "project_id": "project-1", "title": "Roadmap", "created_at": timestamp, "status": "ACTIVE", "mission_ids": []},
            "mission": {"schema_version": 1, "mission_id": "mission-1", "project_id": "project-1", "roadmap_id": "roadmap-1", "objective": "Objective", "created_at": timestamp, "status": "PLANNED"},
            "task": {"schema_version": 1, "task_id": "task-1", "mission_id": "mission-1", "title": "Task", "created_at": timestamp, "status": "PENDING"},
            "action": {"schema_version": 1, "action_id": "action-1", "task_id": "task-1", "operation_id": "operation-1", "idempotency_key": "key-1", "kind": "inspect", "created_at": timestamp, "started_at": None, "completed_at": None, "state": "CREATED", "retry_count": 0, "result": None, "error": None},
            "verification": {"schema_version": 1, "verification_id": "verification-1", "action_id": "action-1", "status": "NOT_TESTED", "verified_at": timestamp, "evidence": [], "reason": None},
            "checkpoint": {"schema_version": 1, "checkpoint_id": "checkpoint-1", "project_id": "project-1", "roadmap_id": "roadmap-1", "mission_id": "mission-1", "task_id": "task-1", "action_id": "action-1", "created_at": timestamp, "lifecycle_state": "PAUSED", "completed_steps": ["plan"], "in_progress_step": "verify", "pause_reason": "resource pressure", "next_action": "resume verify", "backend_id": None, "model_id": None, "active_capabilities": [], "operation_id": "operation-1", "payload": {}},
            "resource_state": {"schema_version": 1, "resource_state_id": "resource-1", "state": "WAITING", "observed_at": timestamp, "source": "test", "snapshot": {}, "reason": None},
            "capability": {"schema_version": 1, "capability_id": "capability-1", "name": "filesystem.read", "granted": False, "scope": [], "granted_at": None, "revoked_at": None},
            "audit_event": {"schema_version": 1, "event_id": "event-1", "event_type": "TEST", "actor": "test", "project_id": "project-1", "mission_id": "mission-1", "action_id": "action-1", "occurred_at": timestamp, "result": "PASS", "reason": None, "correlation_id": "corr-1", "data": {}},
            "benchmark_result": {"schema_version": 1, "benchmark_id": "benchmark-1", "backend_id": "fake", "model_id": "fixture", "started_at": timestamp, "finished_at": None, "status": "RUNNING", "metrics": {}, "environment": {}},
            "model_backend": {"schema_version": 1, "backend_id": "fake", "name": "fixture", "version": "1", "model_id": "fixture", "capabilities": [], "local_only": True, "registered_at": timestamp, "status": "AVAILABLE"},
        }

    def test_all_v1_schemas_validate(self) -> None:
        documents = self.documents()
        self.assertEqual(len(self.registry.names()), 12)
        self.registry.validate_many(documents.items())

    def test_missing_required_and_unknown_properties_are_rejected(self) -> None:
        project = self.documents()["project"]
        del project["project_id"]
        with self.assertRaises(SchemaValidationError):
            self.registry.validate("project", project)

        project = self.documents()["project"]
        project["unexpected"] = True
        with self.assertRaises(SchemaValidationError):
            self.registry.validate("project", project)

    def test_unknown_and_unsupported_versions_are_controlled(self) -> None:
        future = self.documents()["project"]
        future["schema_version"] = 99
        with self.assertRaises(UnknownSchemaVersionError):
            self.registry.validate("project", future)

        old = self.documents()["project"]
        old["schema_version"] = 0
        with self.assertRaises(UnsupportedSchemaVersionError):
            self.registry.validate("project", old)

    def test_atomic_store_preserves_previous_valid_state_on_invalid_save(self) -> None:
        path = self.temp / "project.json"
        store = AtomicJsonStore(path, "project", self.registry)
        valid = self.documents()["project"]
        store.save(valid)
        invalid = dict(valid)
        invalid["status"] = "BROKEN"
        with self.assertRaises(SchemaValidationError):
            store.save(invalid)
        self.assertEqual(store.load(), valid)

    def test_atomic_store_preserves_previous_state_when_interrupted_before_replace(self) -> None:
        path = self.temp / "project.json"
        store = AtomicJsonStore(path, "project", self.registry)
        original = self.documents()["project"]
        replacement = dict(original)
        replacement["status"] = "PAUSED"
        store.save(original)

        def interrupt(_: Path) -> None:
            raise RuntimeError("simulated interruption")

        with self.assertRaises(RuntimeError):
            store.save(replacement, before_replace=interrupt)
        self.assertEqual(store.load(), original)
        self.assertEqual(list(self.temp.glob("*.tmp")), [])

    def test_truncated_json_is_rejected_without_recovery_guess(self) -> None:
        path = self.temp / "project.json"
        path.write_text('{"schema_version": 1, "project_id": "partial"', encoding="utf-8")
        with self.assertRaises(StateCorruptionError):
            AtomicJsonStore(path, "project", self.registry).load()

    def test_checkpoint_contract_round_trips_with_utc(self) -> None:
        now = utc_now()
        checkpoint = CheckpointRecord(
            checkpoint_id="checkpoint-1",
            project_id="project-1",
            roadmap_id="roadmap-1",
            mission_id="mission-1",
            task_id="task-1",
            action_id="action-1",
            created_at=now,
            lifecycle_state="PAUSED",
            completed_steps=("plan",),
            in_progress_step="verify",
            pause_reason="operator pause",
            next_action="resume verify",
            active_capabilities=("filesystem.read",),
        )
        document = checkpoint.to_document()
        self.registry.validate("checkpoint", document)
        restored = CheckpointRecord.from_document(document)
        self.assertEqual(restored.checkpoint_id, checkpoint.checkpoint_id)
        self.assertEqual(restored.created_at.tzinfo, timezone.utc)

    def test_ids_are_stable_and_scoped(self) -> None:
        first = stable_id("operation", "action-1", "key-1")
        second = stable_id("operation", "action-1", "key-1")
        different = stable_id("operation", "action-1", "key-2")
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)

    def test_timestamps_are_utc_and_naive_time_is_rejected(self) -> None:
        formatted = format_utc(datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc))
        self.assertTrue(formatted.endswith("Z"))
        self.assertEqual(parse_utc(formatted).tzinfo, timezone.utc)
        with self.assertRaises(ValueError):
            format_utc(datetime(2026, 10, 3, 9, 0))

    def test_repeated_operation_is_not_started_twice(self) -> None:
        registry = IdempotencyRegistry()
        first, created = registry.begin("action-1", "key-1")
        repeated, created_again = registry.begin("action-1", "key-1")
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first, repeated)
        completed = registry.complete(first.operation_id, {"status": "ok"})
        repeated_completion = registry.complete(first.operation_id, {"status": "ok"})
        self.assertEqual(completed, repeated_completion)
        self.assertEqual(completed.state, OperationState.COMPLETED)

    def test_conflicting_completion_is_rejected(self) -> None:
        registry = IdempotencyRegistry()
        record, _ = registry.begin("action-1", "key-1")
        registry.complete(record.operation_id, {"status": "ok"})
        with self.assertRaises(RuntimeError):
            registry.complete(record.operation_id, {"status": "different"})

    def test_redaction_handles_nested_values_headers_urls_and_text(self) -> None:
        secret_value = "fixture" + "-secret-value"
        bearer_value = "B" * 24
        data = {
            "password": secret_value,
            "nested": {"authorization": "Bearer " + bearer_value},
            "url": "https://user:pass@example.invalid/path?token=" + secret_value,
            "message": "api_key=" + secret_value,
        }
        redacted = redact(data)
        rendered = json.dumps(redacted)
        self.assertNotIn(secret_value, rendered)
        self.assertNotIn(bearer_value, rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertNotIn(bearer_value, redact_text("Authorization: Bearer " + bearer_value))

    def test_audit_trail_redacts_before_document_use(self) -> None:
        secret_value = "fixture" + "-audit-secret"
        event = AuditEvent(
            "TOOL_RESULT",
            "test",
            "action-1",
            reason="api_key=" + secret_value,
            data={"nested": {"password": secret_value}},
        )
        trail = MemoryAuditTrail()
        trail.append(event)
        document = trail.query()[0].to_document()
        rendered = json.dumps(document)
        self.assertNotIn(secret_value, rendered)
        self.registry.validate("audit_event", document)
        direct_rendered = json.dumps(event.to_document())
        self.assertNotIn(secret_value, direct_rendered)

    def test_action_document_from_idempotency_record_is_schema_valid(self) -> None:
        registry = IdempotencyRegistry()
        record, _ = registry.begin("action-1", "key-1")
        document = record.to_action_document("task-1", "inspect")
        self.registry.validate("action", document)


if __name__ == "__main__":
    unittest.main()
