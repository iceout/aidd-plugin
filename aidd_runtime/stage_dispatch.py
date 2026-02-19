from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from aidd_runtime import command_runner, ide_profiles, runtime
from aidd_runtime.resources import DEFAULT_PROJECT_SUBDIR


@dataclass(frozen=True)
class DispatchSpec:
    command: str
    stage: str | None
    entrypoint: str
    ticket_required: bool = True
    inject_ticket_flag: bool = True
    requires_workflow: bool = True
    set_feature: bool = True
    set_stage: bool = True


@dataclass(frozen=True)
class DispatchTarget:
    raw_command: str
    requested_command: str
    resolved_command: str
    is_legacy_alias: bool
    spec: DispatchSpec


@dataclass(frozen=True)
class DispatchResult:
    target: DispatchTarget
    profile: str
    ticket: str | None
    workspace_root: Path
    project_root: Path
    returncode: int
    stdout: str
    stderr: str
    command: tuple[str, ...]


_SEPARATOR_TABLE = str.maketrans({"_": "-", " ": "-", "\t": "-", "\n": "-", "\r": "-"})

DISPATCH_SPECS: dict[str, DispatchSpec] = {
    "aidd-init-flow": DispatchSpec(
        command="aidd-init-flow",
        stage=None,
        entrypoint="skills/aidd-init/runtime/init.py",
        ticket_required=False,
        inject_ticket_flag=False,
        requires_workflow=False,
        set_feature=False,
        set_stage=False,
    ),
    "idea-new": DispatchSpec(
        command="idea-new",
        stage="idea",
        entrypoint="skills/idea-new/runtime/analyst_check.py",
    ),
    "researcher": DispatchSpec(
        command="researcher",
        stage="research",
        entrypoint="skills/researcher/runtime/research.py",
    ),
    "plan-new": DispatchSpec(
        command="plan-new",
        stage="plan",
        entrypoint="skills/plan-new/runtime/research_check.py",
    ),
    "review-spec": DispatchSpec(
        command="review-spec",
        stage="review-spec",
        entrypoint="skills/review-spec/runtime/prd_review_cli.py",
    ),
    "spec-interview": DispatchSpec(
        command="spec-interview",
        stage="spec-interview",
        entrypoint="skills/spec-interview/runtime/spec_interview.py",
    ),
    "tasks-new": DispatchSpec(
        command="tasks-new",
        stage="tasklist",
        entrypoint="skills/tasks-new/runtime/tasks_new.py",
    ),
    "implement": DispatchSpec(
        command="implement",
        stage="implement",
        entrypoint="skills/implement/runtime/implement_run.py",
    ),
    "review": DispatchSpec(
        command="review",
        stage="review",
        entrypoint="skills/review/runtime/review_run.py",
    ),
    "qa": DispatchSpec(
        command="qa",
        stage="qa",
        entrypoint="skills/qa/runtime/qa.py",
    ),
}

LEGACY_COMMAND_ALIASES: dict[str, str] = {
    "aidd-idea-flow": "idea-new",
    "aidd-research-flow": "researcher",
    "aidd-plan-flow": "plan-new",
    "aidd-implement-flow": "implement",
    "aidd-review-flow": "review",
    "aidd-qa-flow": "qa",
    "aidd-init": "aidd-init-flow",
}


def normalize_command_name(command: str, profile: str | ide_profiles.IdeProfile | None = None) -> str:
    profile_cfg = _resolve_profile(command, profile)
    raw = ide_profiles.strip_host_prefix(command, profile_cfg)
    if not raw:
        return ""
    normalized = raw.strip().lower().translate(_SEPARATOR_TABLE)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


def resolve_dispatch_target(
    command: str,
    *,
    profile: str | ide_profiles.IdeProfile | None = None,
) -> DispatchTarget:
    requested = normalize_command_name(command, profile=profile)
    if not requested:
        raise ValueError("command name is required")

    resolved = LEGACY_COMMAND_ALIASES.get(requested, requested)
    spec = DISPATCH_SPECS.get(resolved)
    if spec is None:
        supported = ", ".join(sorted(DISPATCH_SPECS))
        raise ValueError(f"unsupported stage command '{command}'. Supported: {supported}")

    return DispatchTarget(
        raw_command=command,
        requested_command=requested,
        resolved_command=resolved,
        is_legacy_alias=(resolved != requested),
        spec=spec,
    )


def dispatch_stage_command(
    command: str,
    *,
    ticket: str | None = None,
    argv: Sequence[str] | None = None,
    cwd: Path | None = None,
    profile: str | ide_profiles.IdeProfile | None = None,
    check: bool = False,
) -> DispatchResult:
    profile_cfg = _resolve_profile(command, profile)
    target = resolve_dispatch_target(command, profile=profile_cfg)
    plugin_root = runtime.require_plugin_root()
    env = command_runner.build_runtime_env(plugin_root, profile=profile_cfg)

    workspace_root: Path
    project_root: Path
    if target.spec.requires_workflow:
        workspace_root, project_root = runtime.require_workflow_root(cwd)
    else:
        workspace_root = (cwd or Path.cwd()).resolve()
        project_root = workspace_root / DEFAULT_PROJECT_SUBDIR

    effective_ticket = _resolve_ticket(project_root, ticket=ticket)
    if target.spec.ticket_required and not effective_ticket:
        raise ValueError(
            f"ticket is required for '{target.resolved_command}'; pass ticket or set docs/.active.json first."
        )

    if target.spec.set_feature and effective_ticket:
        _run_state_script(
            plugin_root,
            script="set_active_feature.py",
            args=[effective_ticket],
            cwd=workspace_root,
            profile=profile_cfg,
            env=env,
        )
    if target.spec.set_stage and target.spec.stage:
        _run_state_script(
            plugin_root,
            script="set_active_stage.py",
            args=[target.spec.stage],
            cwd=workspace_root,
            profile=profile_cfg,
            env=env,
        )

    script_path = (plugin_root / target.spec.entrypoint).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"entrypoint not found: {script_path}")

    stage_argv = list(argv or [])
    if (
        target.spec.inject_ticket_flag
        and effective_ticket
        and not _contains_flag(stage_argv, "--ticket")
    ):
        stage_argv = ["--ticket", effective_ticket, *stage_argv]

    command_list = [sys.executable, str(script_path), *stage_argv]
    command_result = command_runner.run_command(
        command_list,
        cwd=workspace_root,
        profile=profile_cfg,
        env=env,
        check=check,
        error_context=f"dispatch failed for '{target.resolved_command}'",
    )

    return DispatchResult(
        target=target,
        profile=profile_cfg.name,
        ticket=effective_ticket,
        workspace_root=workspace_root,
        project_root=project_root,
        returncode=command_result.returncode,
        stdout=command_result.stdout,
        stderr=command_result.stderr,
        command=command_result.command,
    )


def _resolve_ticket(project_root: Path, *, ticket: str | None) -> str | None:
    provided = (ticket or "").strip()
    if provided:
        return provided
    existing = runtime.read_active_ticket(project_root).strip()
    return existing or None


def _contains_flag(argv: Sequence[str], flag: str) -> bool:
    if flag in argv:
        return True
    prefix = f"{flag}="
    return any(item.startswith(prefix) for item in argv)


def _run_state_script(
    plugin_root: Path,
    *,
    script: str,
    args: Sequence[str],
    cwd: Path,
    profile: ide_profiles.IdeProfile,
    env: dict[str, str],
) -> None:
    script_path = plugin_root / "skills" / "aidd-flow-state" / "runtime" / script
    if not script_path.exists():
        raise FileNotFoundError(f"state script not found: {script_path}")
    command_runner.run_python(
        script_path,
        argv=args,
        cwd=cwd,
        profile=profile,
        env=env,
        check=True,
        error_context=f"state transition via {script} failed",
    )


def _resolve_profile(
    command: str,
    profile: str | ide_profiles.IdeProfile | None,
) -> ide_profiles.IdeProfile:
    return ide_profiles.select_profile(command, profile=profile)
