from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from aidd_runtime import command_runner, runtime


@dataclass(frozen=True)
class GateResult:
    name: str
    returncode: int
    output: str = ""
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_analyst_gate(
    root: Path,
    *,
    ticket: str,
    branch: str | None = None,
) -> GateResult:
    from aidd_runtime.analyst_guard import AnalystValidationError, load_settings, validate_prd

    settings = load_settings(root)
    try:
        summary = validate_prd(root, ticket, settings=settings, branch=branch)
    except AnalystValidationError as exc:
        return GateResult(name="analyst_check", returncode=2, output=str(exc))
    if summary.status is None:
        return GateResult(
            name="analyst_check",
            returncode=0,
            output="analyst gate skipped.",
            skipped=True,
        )
    return GateResult(
        name="analyst_check",
        returncode=0,
        output=f"analyst gate OK (status: {summary.status}, questions: {summary.question_count}).",
    )


def run_research_gate(
    root: Path,
    *,
    ticket: str,
    branch: str | None = None,
) -> GateResult:
    from aidd_runtime.research_guard import ResearchValidationError, load_settings, validate_research

    settings = load_settings(root)
    try:
        summary = validate_research(root, ticket, settings=settings, branch=branch)
    except ResearchValidationError as exc:
        return GateResult(name="research_check", returncode=2, output=str(exc))
    if summary.skipped_reason == "pending-baseline":
        return GateResult(
            name="research_check",
            returncode=0,
            output="research gate skipped (pending-baseline).",
            skipped=True,
        )
    if summary.status is None:
        reason = summary.skipped_reason or "disabled"
        return GateResult(
            name="research_check",
            returncode=0,
            output=f"research gate skipped ({reason}).",
            skipped=True,
        )
    details: list[str] = [f"status: {summary.status}"]
    if summary.path_count is not None:
        details.append(f"paths: {summary.path_count}")
    if summary.age_days is not None:
        details.append(f"age: {summary.age_days}d")
    return GateResult(
        name="research_check",
        returncode=0,
        output=f"research gate OK ({', '.join(details)}).",
    )


def run_tasklist_check(
    root: Path,
    *,
    ticket: str,
    slug_hint: str = "",
    branch: str | None = None,
) -> GateResult:
    from aidd_runtime import tasklist_check

    args = ["--ticket", ticket, "--quiet-ok"]
    if slug_hint:
        args.extend(["--slug-hint", slug_hint])
    if branch:
        args.extend(["--branch", branch])
    status, output = _run_with_capture(lambda: tasklist_check.run_check(tasklist_check.parse_args(args)))
    return GateResult(name="tasklist_check", returncode=status, output=output)


def run_plan_review_gate(
    root: Path,
    *,
    ticket: str,
    file_path: str = "",
    branch: str | None = None,
) -> GateResult:
    from aidd_runtime import plan_review_gate

    args = ["--ticket", ticket, "--skip-on-plan-edit"]
    if file_path:
        args.extend(["--file-path", file_path])
    if branch:
        args.extend(["--branch", branch])
    status, output = _run_with_capture(lambda: plan_review_gate.run_gate(plan_review_gate.parse_args(args)))
    return GateResult(name="plan_review_gate", returncode=status, output=output)


def run_prd_review_gate(
    root: Path,
    *,
    ticket: str,
    slug_hint: str = "",
    file_path: str = "",
    branch: str | None = None,
) -> GateResult:
    from aidd_runtime import prd_review_gate

    args = ["--ticket", ticket, "--skip-on-prd-edit"]
    if slug_hint:
        args.extend(["--slug-hint", slug_hint])
    if file_path:
        args.extend(["--file-path", file_path])
    if branch:
        args.extend(["--branch", branch])
    status, output = _run_with_capture(lambda: prd_review_gate.run_gate(prd_review_gate.parse_args(args)))
    return GateResult(name="prd_review_gate", returncode=status, output=output)


def run_diff_boundary_check(
    root: Path,
    *,
    ticket: str,
    allowed: str | None = None,
) -> GateResult:
    from aidd_runtime import diff_boundary_check

    work_item_key = runtime.read_active_work_item(root)
    if not work_item_key:
        return GateResult(
            name="diff_boundary_check",
            returncode=0,
            output="diff-boundary-check skipped (no active work_item).",
            skipped=True,
        )

    scope_key = runtime.resolve_scope_key(work_item_key, ticket)
    loop_pack_path = root / "reports" / "loops" / ticket / f"{scope_key}.loop.pack.md"
    if not loop_pack_path.exists():
        return GateResult(
            name="diff_boundary_check",
            returncode=0,
            output=(
                "diff-boundary-check skipped "
                f"(loop pack missing: {runtime.rel_path(loop_pack_path, root)})."
            ),
            skipped=True,
        )

    args = ["--ticket", ticket, "--loop-pack", runtime.rel_path(loop_pack_path, root)]
    if allowed:
        args.extend(["--allowed", allowed])
    status, output = _run_with_capture(lambda: diff_boundary_check.main(args))
    return GateResult(name="diff_boundary_check", returncode=status, output=output)


def run_qa_gate(
    root: Path,
    *,
    ticket: str,
    slug_hint: str = "",
    branch: str | None = None,
    extra_argv: Sequence[str] | None = None,
) -> GateResult:
    plugin_root = runtime.require_plugin_root()
    env = command_runner.build_runtime_env(plugin_root)
    script_path = plugin_root / "skills" / "qa" / "runtime" / "qa.py"
    workspace_root = root.parent if root.name == "aidd" else root

    qa_args = ["--ticket", ticket, "--gate"]
    if slug_hint:
        qa_args.extend(["--slug-hint", slug_hint])
    if branch:
        qa_args.extend(["--branch", branch])
    if extra_argv:
        qa_args.extend(list(extra_argv))

    result = command_runner.run_python(
        script_path,
        argv=qa_args,
        cwd=workspace_root,
        env=env,
        check=False,
    )
    output = _join_output(result.stdout, result.stderr)
    return GateResult(name="qa_gate", returncode=result.returncode, output=output)


def run_stage_preflight(
    root: Path,
    *,
    ticket: str,
    slug_hint: str = "",
    stage: str,
    branch: str | None = None,
    file_path: str = "",
) -> GateResult:
    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in {"implement", "review", "qa"}:
        return GateResult(name="preflight", returncode=0, output="")

    sequence = [
        lambda: run_analyst_gate(root, ticket=ticket, branch=branch),
        lambda: run_plan_review_gate(root, ticket=ticket, file_path=file_path, branch=branch),
        lambda: run_prd_review_gate(
            root,
            ticket=ticket,
            slug_hint=slug_hint,
            file_path=file_path,
            branch=branch,
        ),
        lambda: run_research_gate(root, ticket=ticket, branch=branch),
        lambda: run_tasklist_check(
            root,
            ticket=ticket,
            slug_hint=slug_hint,
            branch=branch,
        ),
    ]
    if normalized_stage in {"implement", "review"}:
        sequence.append(lambda: run_diff_boundary_check(root, ticket=ticket))

    for invoke in sequence:
        gate_result = invoke()
        if not gate_result.ok:
            return gate_result
    return GateResult(name="preflight", returncode=0, output="preflight gates passed.")


def _run_with_capture(invoke) -> tuple[int, str]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            status = int(invoke())
    except Exception as exc:
        return 2, str(exc)
    output = _join_output(stdout_buf.getvalue(), stderr_buf.getvalue())
    return status, output


def _join_output(stdout_text: str, stderr_text: str) -> str:
    parts = [stdout_text.strip(), stderr_text.strip()]
    return "\n".join(part for part in parts if part).strip()
