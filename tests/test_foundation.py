from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import unittest

from localcoder.audit import AuditEvent, MemoryAuditTrail
from localcoder.capabilities import Capability, CapabilityPolicy
from localcoder.checkpoints import Checkpoint
from localcoder.core import GenerationRequest, MissionState, ResourceState
from localcoder.mission_engine import MissionSpec
from localcoder.project import ProjectSpec
from localcoder.resource_manager import ResourceSnapshot


class FoundationTests(unittest.TestCase):
    def test_required_resource_states_are_explicit(self) -> None:
        self.assertEqual(
            {state.value for state in ResourceState},
            {"WORKING", "PAUSING", "SLEEPING", "RESUMING", "ERROR", "WAITING"},
        )

    def test_request_rejects_empty_prompt(self) -> None:
        with self.assertRaises(ValueError):
            GenerationRequest(" ")

    def test_capability_policy_denies_by_default(self) -> None:
        policy = CapabilityPolicy()
        self.assertFalse(policy.allows(Capability.PROCESS_EXECUTION))
        self.assertTrue(
            CapabilityPolicy(frozenset({Capability.FILESYSTEM_READ})).allows(
                Capability.FILESYSTEM_READ
            )
        )

    def test_mission_contains_scope_and_acceptance(self) -> None:
        mission = MissionSpec(
            mission_id="001",
            objective="Establish foundation",
            scope=("contracts",),
            out_of_scope=("autonomous execution",),
            acceptance_criteria=("tests pass",),
            rollback=("remove local foundation commit",),
        )
        self.assertEqual(mission.mission_id, "001")
        self.assertIn("autonomous execution", mission.out_of_scope)

    def test_audit_trail_is_append_only_for_memory_adapter(self) -> None:
        trail = MemoryAuditTrail()
        event = AuditEvent("MISSION_STARTED", "test", "mission:001")
        trail.append(event)
        self.assertEqual(trail.query("mission:001"), (event,))

    def test_data_models_are_constructible(self) -> None:
        now = datetime.now(timezone.utc)
        snapshot = ResourceSnapshot(observed_at=now, ram_total_bytes=100, ram_available_bytes=40)
        checkpoint = Checkpoint("cp-1", "demo", "001", now, "audit")
        project = ProjectSpec("demo", "E:\\demo", "roadmap.md")
        self.assertEqual(snapshot.ram_available_bytes, 40)
        self.assertEqual(checkpoint.step, "audit")
        self.assertEqual(project.roadmap_path, "roadmap.md")
        self.assertEqual(MissionState.PLANNED.value, "PLANNED")


if __name__ == "__main__":
    unittest.main()
