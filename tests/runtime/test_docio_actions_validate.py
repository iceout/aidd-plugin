from __future__ import annotations

from aidd_runtime import actions_validate


def test_validate_actions_v1_success() -> None:
    payload = {
        "schema_version": "aidd.actions.v1",
        "stage": "implement",
        "ticket": "DEMO-1",
        "scope_key": "iteration_id_I1",
        "work_item_key": "iteration_id=I1",
        "allowed_action_types": [
            "tasklist_ops.set_iteration_done",
            "tasklist_ops.append_progress_log",
        ],
        "actions": [
            {
                "type": "tasklist_ops.set_iteration_done",
                "params": {"item_id": "I1"},
            },
            {
                "type": "tasklist_ops.append_progress_log",
                "params": {
                    "date": "2026-02-20",
                    "source": "implement",
                    "item_id": "I1",
                    "kind": "iteration",
                    "hash": "abc123",
                    "msg": "done",
                },
            },
        ],
    }
    assert actions_validate.validate_actions_data(payload) == []


def test_validate_actions_v1_rejects_unsupported_allowed_type() -> None:
    payload = {
        "schema_version": "aidd.actions.v1",
        "stage": "implement",
        "ticket": "DEMO-1",
        "scope_key": "iteration_id_I1",
        "work_item_key": "iteration_id=I1",
        "allowed_action_types": ["foo.bar"],
        "actions": [],
    }
    errors = actions_validate.validate_actions_data(payload)
    assert any("allowed_action_types contains unsupported values" in err for err in errors)


def test_validate_actions_requires_known_schema_version() -> None:
    errors = actions_validate.validate_actions_data({"schema_version": "aidd.actions.v9"})
    assert errors
    assert "schema_version must be one of" in errors[0]
