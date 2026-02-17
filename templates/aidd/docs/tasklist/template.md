---
Ticket: <ABC-123>
Slug: <short-slug>
# Status: PENDING|READY|WARN|BLOCKED
Status: PENDING
Updated: <YYYY-MM-DD>
Owner: <name/team>
PRD: aidd/docs/prd/<ABC-123>.prd.md
Plan: aidd/docs/plan/<ABC-123>.md
Research: aidd/docs/research/<ABC-123>.md
Spec: aidd/docs/spec/<ABC-123>.spec.yaml
Reports:
  tests: aidd/reports/tests/<ABC-123>/<scope_key>.jsonl  # optional
  review_report: aidd/reports/reviewer/<ABC-123>/<scope_key>.json
  reviewer_marker: aidd/reports/reviewer/<ABC-123>/<scope_key>.tests.json
  qa: aidd/reports/qa/<ABC-123>.json
---

# Tasklist: <ABC-123> — <short-slug>

> Single source of truth for implement/review/qa.
> Always read in this order: `## AIDD:CONTEXT_PACK`, then `## AIDD:SPEC_PACK`, `## AIDD:TEST_EXECUTION`, `## AIDD:ITERATIONS_FULL`, and finally `## AIDD:NEXT_3`.

## AIDD:CONTEXT_PACK
Updated: <YYYY-MM-DD>
Ticket: <ABC-123>
Stage: <idea|research|plan|review-spec|review-plan|review-prd|spec-interview|tasklist|implement|review|qa|status>
Status: PENDING

### TL;DR
- Goal: <1–2 sentences>
- Current focus (1 checkbox): <exact name from AIDD:NEXT_3>
- Done since last pack: <1–3 concise bullet points>
- Risk level: <low|medium|high> — <1-line justification>

### Scope & boundaries
- Allowed paths (patch boundaries):
  - <path1/>
  - <path2/>
- Forbidden / out of scope:
  - <pathX/> — <reason>
- Integrations / dependencies:
  - <api/service/db/topic> — <key note>

### Decisions & defaults (living)
- Feature flag: <none|flag_name + default>
- Contract/API: <link to spec or 1-line summary>
- Data model changes: <none|describe schema updates>
- Observability: <expected logs/metrics/tracing>

### Test policy (iteration budget)
- Cadence: <on_stop|checkpoint|manual>
- Profile: <fast|targeted|full|none>
- Tasks: <e.g., :module:test or npm test ...> (for targeted/full)
- Filters: <if applicable>
- Budget minutes: <N>
- Known flaky / failing: <none|link to aidd/reports/tests/...>

### Commands quickstart (copy/paste)
- Format: <hook handles it | command>
- Tests (manual): <command for targeted/full>
- Run/Dev: <command / URL / emulator / device steps> (optional)

### Open questions / blockers
- Q1: <...>
- Q2: <...>

### Blockers summary (handoff)
- <handoff-id> — <1 line describing the blocker>

### References
- Spec: aidd/docs/spec/<ABC-123>.spec.yaml
- PRD: aidd/docs/prd/<ABC-123>.prd.md (see #AIDD:ACCEPTANCE, #AIDD:ROLL_OUT)
- Research: aidd/docs/research/<ABC-123>.md (see #AIDD:INTEGRATION_POINTS)
- Plan: aidd/docs/plan/<ABC-123>.md (see #AIDD:FILES_TOUCHED, #AIDD:ITERATIONS)
- Reports:
  - review_report: aidd/reports/reviewer/<ABC-123>/<scope_key>.json
  - reviewer_marker: aidd/reports/reviewer/<ABC-123>/<scope_key>.tests.json
  - qa: aidd/reports/qa/<ABC-123>.json

---

## AIDD:SPEC_PACK
Updated: <YYYY-MM-DD>
Spec: aidd/docs/spec/<ABC-123>.spec.yaml (status: <draft|ready>|none)
- Goal: <1–2 sentences>
- Non-goals:
  - <...>
- Key decisions:
  - <...>
- Risks:
  - <...>

## AIDD:TEST_STRATEGY
- Unit: <scope>
- Integration: <scope>
- Contract: <scope>
- E2E/Stand: <critical paths>
- Test data: <fixtures/mocks>

---

## AIDD:TEST_EXECUTION
> Concrete commands/filters (execution level).
- profile: <fast|targeted|full|none>
- tasks: <commands/tasks>
- filters: <filters>
- when: <on_stop|checkpoint|manual>
- reason: <why this profile>

---

## AIDD:ITERATIONS_FULL
> Exhaustive list of implementation iterations (1..N). Must be **more detailed than the plan** and leave no gaps.
> Canonical iteration format: `- [ ] I7: <title> (iteration_id: I7)`
- [ ] I1: <short title> (iteration_id: I1)
  - parent_iteration_id: <I0|none>  # optional
  - Goal: <precise outcome>
  - Outputs: <iteration artifacts>
  - DoD: <how we verify readiness>
  - Boundaries: <paths/modules + what stays untouched>
  - Priority: <low|medium|high>  # optional
  - Blocking: <true|false>       # optional
  - deps: []
  - locks: []
  - Expected paths:
    - <path1/**>
    - <path2/**>
  - Size budget:
    - max_files: <N>
    - max_loc: <N>
  - Commands:
    - <doc/ref or command>
  - Exit criteria:
    - <criterion 1>
    - <criterion 2>
  - Steps:
    - <step 1>
    - <step 2>
    - <step 3>
  - Tests:
    - profile: <fast|targeted|full|none>
    - tasks: <commands/tasks>
    - filters: <filters>
  - Acceptance mapping: <AC-1, spec:...>
  - Risks & mitigations: <risk → mitigation>
  - Dependencies: <services/feature flags/data>
- [ ] I2: <...> (iteration_id: I2)
  - parent_iteration_id: <I1|none>  # optional
  - Goal: <...>
  - Outputs: <...>
  - DoD: <...>
  - Boundaries: <...>
  - Priority: <low|medium|high>  # optional
  - Blocking: <true|false>       # optional
  - deps: []
  - locks: []
  - Expected paths:
    - <path1/**>
  - Size budget:
    - max_files: <N>
    - max_loc: <N>
  - Commands:
    - <doc/ref or command>
  - Exit criteria:
    - <...>
  - Steps:
    - <...>
  - Tests:
    - profile: <fast|targeted|full|none>
    - tasks: <...>
    - filters: <...>
  - Acceptance mapping: <...>
  - Risks & mitigations: <...>
  - Dependencies: <...>
<!-- Add I3..N as needed, following the same structure. -->

---

## AIDD:NEXT_3
> The next 3 implement checkboxes. Pointer list only: 1–2 lines plus `ref:` to the detailed section.
- [ ] I1: <current step summary> (ref: iteration_id=I1)
- [ ] I2: <next step> (ref: iteration_id=I2)

---

## AIDD:OUT_OF_SCOPE_BACKLOG
> Ideas/tasks that DO NOT belong to this work item (keep scope tight).
- [ ] <idea/task> (source: implement|review|qa|research|manual)

---

## AIDD:HANDOFF_INBOX
> Collect inbound work from Research/Review/QA (source: aidd/reports/...).
> Required format:
> Canonical: `- [ ] <title> (id: review:F6) (Priority: high) (Blocking: true)`
> Source blocks are inserted by derive (`<!-- handoff:<source> start --> ... <!-- end -->`).
> Manual tasks stay in `handoff:manual` so derive/normalize will not touch them.
> Example (non-active):
> - [ ] <title> (id: review:F6) (Priority: high) (Blocking: true)
>   - source: review|qa|research|manual
>   - Report: <aidd/reports/...>
>   - Status: open|done|blocked
>   - scope: iteration_id|n/a
>   - DoD: <how to confirm it is fixed>
>   - Boundaries:
>     - must-touch: ["path1", "path2"]
>     - must-not-touch: ["pathX"]
>   - Tests:
>     - profile: fast|targeted|full|none
>     - tasks: ["..."]
>     - filters: ["..."]
>   - Notes: <trade-offs/risks/why it matters>

<!-- handoff:manual start -->
<!-- handoff:manual end -->

> Additional examples (inactive):
> - [ ] Critical null check in webhook handler (id: review:null-check) (Priority: high) (Blocking: true)
>   - source: review
>   - Review report: aidd/reports/reviewer/<ticket>/<scope_key>.json
>   - Reviewer marker: aidd/reports/reviewer/<ticket>/<scope_key>.tests.json
>   - Status: open
>   - scope: I2
>   - DoD: webhook rejects empty payload with 4xx + unit test updated
>   - Boundaries:
>     - must-touch: ["src/webhooks/", "tests/webhooks/"]
>     - must-not-touch: ["infra/"]
>   - Tests:
>     - profile: targeted
>     - tasks: ["pytest tests/webhooks/test_handler.py"]
>     - filters: []
>   - Notes: prevents silent 500 on missing payload
> - [ ] AC-3 export fails on empty data (id: qa:export-empty) (Priority: high) (Blocking: true)
>   - source: qa
>   - Report: aidd/reports/qa/<ticket>.json
>   - Status: open
>   - scope: n/a
>   - DoD: export returns empty CSV with headers + QA traceability updated
>   - Boundaries:
>     - must-touch: ["src/export/"]
>     - must-not-touch: ["db/schema-changes/"]
>   - Tests:
>     - profile: fast
>     - tasks: []
>     - filters: []
>   - Notes: blocks release for AC-3

---

## AIDD:QA_TRACEABILITY
> AC → check → result → evidence.
- AC-1 → <check> → <met|not-met|not-verified> → <evidence/link>
- AC-2 → <check> → <met|not-met|not-verified> → <evidence/link>

---

## AIDD:CHECKLIST

### AIDD:CHECKLIST_SPEC
- [ ] PRD: Status READY (no unresolved blocker questions)
- [ ] Research: Status reviewed
- [ ] Plan: exists and is valid
- [ ] Review Spec: Plan Review READY + PRD Review READY
- [ ] Spec interview (optional): spec updated; then run `/feature-dev-aidd:tasks-new` to sync the tasklist

### AIDD:CHECKLIST_IMPLEMENT
- [ ] Functionality shipped for checkbox #1 from AIDD:NEXT_3
- [ ] Tests added/updated per plan
- [ ] `AIDD:CONTEXT_PACK` updated (scope + test policy)
- [ ] `AIDD:TEST_EXECUTION` updated (if test tactics changed)
- [ ] Progress logged (see AIDD:PROGRESS_LOG)

### AIDD:CHECKLIST_REVIEW
- [ ] Reviewer findings copied into the tasklist (handoff)
- [ ] Test requirements updated (if reviewer marker is used)
- [ ] Changes match plan/PRD (no scope creep)

### AIDD:CHECKLIST_QA
- [ ] QA verified `AIDD:ACCEPTANCE` (traceability)
- [ ] QA report stored (aidd/reports/qa/<ticket>.json)
- [ ] Known issues documented

### AIDD:CHECKLIST_RELEASE
- [ ] Release notes / changelog (if required)
- [ ] Deploy to environment (env + version + time)
- [ ] Smoke / e2e (if available)
- [ ] Monitoring/alerts/dashboards checked

### AIDD:CHECKLIST_POST_RELEASE
- [ ] Rollback plan reviewed (if relevant)
- [ ] Success/guardrail metrics captured
- [ ] Tech debt / follow-up tasks recorded

---

## AIDD:PROGRESS_LOG
> Mini log: record quick entries after every iteration.
> Format:
> `- YYYY-MM-DD source=implement id=I4 kind=iteration hash=abc123 link=aidd/reports/tests/<ticket>/<scope_key>.jsonl msg=short-note`
> `- YYYY-MM-DD source=review id=review:F6 kind=handoff hash=def456 link=aidd/reports/reviewer/<ticket>/<scope_key>.json msg=blocked`
- YYYY-MM-DD source=implement id=I1 kind=iteration hash=abc123 link=aidd/reports/tests/<ticket>/<scope_key>.jsonl msg=...

---

## AIDD:HOW_TO_UPDATE
- Iteration rule: **1 checkbox** (or 2 tightly related ones) → Stop.
- Mark checkboxes like this:
  - `- [x] I1: <title> (iteration_id: I1) (link: <commit/pr|report>)`
  - `- [x] <handoff title> (id: review:F6) (link: <commit/pr|report>)`
- After every `[x]`, refresh `AIDD:NEXT_3` (pointer list) and add an entry to `AIDD:PROGRESS_LOG`.
- When test profiles/commands change, update `AIDD:TEST_EXECUTION`.
- If the spec changes, run `/feature-dev-aidd:tasks-new` to synchronize the tasklist.
- Do not paste raw logs/stack traces here—store them under `aidd/reports/**` and link them.
