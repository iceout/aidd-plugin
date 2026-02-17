# PRD — Template

Fill out the sections according to the project. Examples in parentheses illustrate the expected format.

Status: draft
Ticket: <ticket>
Updated: YYYY-MM-DD

## Analyst dialogue

Research reference: `aidd/docs/research/<ticket>.md`

> This section is created automatically after `/feature-dev-aidd:idea-new <ticket>` — capture each Q/A pair and update the status to READY before `analyst-check`.

Question 1 (Blocker|Clarification): `<What needs clarification?>`  
Why: `<Which decision/section is blocked?>`  
Options: `A) ... B) ...`  
Default: `<What to assume until clarified?>`  
Answer 1: `<Response or TBD>`

<!-- Add more “Question N / Answer N” pairs as needed. Remove the guidance once populated. -->

## AIDD:ANSWERS
> Unified format for answers gathered in chat (duplicate inside “Analyst dialogue” if necessary).
> Answer ids must match `Q` ids from `AIDD:OPEN_QUESTIONS`.
- Answer 1: <answer>
- Answer 2: <answer>

## AIDD:RESEARCH_HINTS
> Mandatory for `/feature-dev-aidd:researcher`: provide at least `Paths` or `Keywords`.
> Research returns `BLOCK` if both fields are blank.
- **Paths**: `<path1:path2>` (e.g., `src/app:src/shared`)
- **Keywords**: `<kw1,kw2>` (e.g., `payment,checkout`)
- **Notes**: `<what to inspect or validate>`

## AIDD:CONTEXT_PACK
- `<short context, ≤ 20 lines>`

## AIDD:NON_NEGOTIABLES
- `<what cannot change>`

## AIDD:OPEN_QUESTIONS
- `Q1: <question> → <owner> → <due date>`
- `Q2: <question> → <owner> → <due date>`
> Keep `Q` ids in sync across “Analyst dialogue” and `AIDD:ANSWERS`.
> Reference questions by `Q` id inside the plan/tasklist to avoid duplicating the text.
> When an answer is confirmed inside `AIDD:ANSWERS`, move the entry to `AIDD:DECISIONS` and remove it from `AIDD:OPEN_QUESTIONS`.

## AIDD:RISKS
- `<risk> → <mitigation>`

## AIDD:DECISIONS
- `<decision> → <reason>`

## AIDD:GOALS
- `<goal 1>`
- `<goal 2>`

## AIDD:NON_GOALS
- `<non-goal>`

## AIDD:ACCEPTANCE
- `<AC-1>`
- `<AC-2>`

## AIDD:METRICS
- `<metric> → <target>`

## AIDD:ROLL_OUT
- `<phases / flags / rollback>`

## 1. Overview
- **Product/feature name**: `<Name or code>` (e.g., `Smart Checkout`)
- **Source artifacts**: `<List of repository docs>` (e.g., `aidd/docs/.active.json (slug_hint)`, `aidd/docs/research/ABC-123.md`, `aidd/reports/research/ABC-123-rlm.pack.json`)
- **Date/version**: `<2024-05-14 v1>`
- **Brief description**: `<1–2 sentences about the initiative>`

## 2. Context and problems
- **Current state**: `<What happens today>` (e.g., “Conversion drops 12% at checkout”)
- **Problems/hypotheses**: `<List of top pain points>`
- **Impacted segments**: `<Segments plus user share>`

## 3. Goals and success metrics
- **North Star / key metric**: `<A → B>` (e.g., “Raise conversion to 68% (+10 pp)”)  
- **Supporting metrics**: `<metric → target>` (e.g., “Cut checkout time to 40 seconds”)
- **Guardrail metrics**: `<metric → threshold>` (e.g., “Payment error rate ≤ 1%”)

## 4. Related ADRs and artifacts
- `<adr/0001-smart-checkout.md — explains protocol choice>`  
- `<adr/0002-payment-gateway.md — covers PSP integration>`  
- `aidd/docs/research/<ticket>.md — Researcher findings and integration suggestions`  
- `<tasks / epics / RFCs>` (add links or ids)

## 5. User scenarios
Describe the primary flows from the user perspective:
1. `<How the user completes the key task>`  
2. `<Edge-case scenario>`  
Add diagrams or sequences if useful.

## 6. Requirements
### 6.1 Functional
- [ ] `<Short behavior description>` (e.g., “System keeps cart drafts for 7 days”)
- [ ] `<Validation or edge cases>`

### 6.2 Non-functional
- [ ] `<SLO/SLI or performance>` (e.g., “Service P95 latency ≤ 300 ms”)
- [ ] `<Security, availability, localization>`

### 6.3 Acceptance criteria
- [ ] `<AC-1: acceptance condition>`
- [ ] `<AC-2: acceptance condition>`

## 7. Constraints and dependencies
- **Technical**: `<Infrastructure, integrations, licenses>`
- **Process**: `<Release calendars, external teams>`
- **External**: `<Partners, regulators>`

## 8. Plan and phases
- **Milestones**: `<MVP, Beta, GA>`
- **Automation & checks**: `<Hooks or commands each stage must run>` (e.g., `<test-runner> <args>`, `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/progress_cli.py --source implement --ticket ABC-123`)
- **System integrations**: `<Services, APIs, queues involved>`

## 9. Risks and strategies
- `<Risk>` → `<Likelihood / impact>` → `<Mitigation>`
- `<What happens if the hypothesis fails>`

## 10. Open questions
- `<Question>` → `<Owner>` → `<Resolution due date>`

## 11. PRD Review
Status: PENDING

### Summary
- `<Key review findings>`

### Findings
- [ ] `<Problem>` — `<Severity>` — `<Recommendation>`

### Action items
- [ ] `<Action>` — `<Owner>` — `<Due date>`

> Update status to `READY` when everything is resolved.

## 12. Change log
- `<Date>` — `<What changed>` — `<Author>`
