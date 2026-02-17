# Implementation Plan — Template

Status: PENDING
PRD: `aidd/docs/prd/<ticket>.prd.md`
Research: `aidd/docs/research/<ticket>.md`

## AIDD:CONTEXT_PACK
- `<brief iteration context>`

## AIDD:NON_NEGOTIABLES
- `<constraints that must not be broken>`

## AIDD:OPEN_QUESTIONS
- `PRD Q1 → <owner> → <due date>`
- `<new question> → <owner> → <due date>`
> If a question already lives in the PRD `AIDD:OPEN_QUESTIONS`, refer to it by id (`PRD QN`) instead of duplicating the text.

## AIDD:ANSWERS
> Unified format for chat answers (if questions exist).
- Answer 1: <answer>
- Answer 2: <answer>

## AIDD:RISKS
- `<risk> → <mitigation>`

## AIDD:DECISIONS
- `<decision> → <why>`

## AIDD:DESIGN
- `<key layers/boundaries>`

## AIDD:FILES_TOUCHED
- `<path/module> — <planned change>`

## AIDD:ITERATIONS
- iteration_id: I1
  - Goal: <iteration goal>
  - Boundaries: <modules/limits>
  - Outputs: <artifacts>
  - DoD: <definition of done>
  - Test categories: <unit|integration|e2e>

## AIDD:TEST_STRATEGY
- `<what / where / how we test>`

## 1. Context and goals
- **Goal:** [short]
- **Scope:** [in/out]
- **Constraints:** [technical/process]

## 2. Design and patterns
- **Layers/boundaries:** [domain/app/infra]
- **Patterns:** [service layer / ports-adapters / other]
- **Reuse:** [shared components]

## 3. Files & modules touched
- [path/module] — [change description]

## 4. Iterations and DoD
### Iteration I1
- Goal: [what we ship]
- Boundaries: [modules/paths touched]
- Outputs: [iteration artifacts]
- DoD: [readiness criteria]
- Test categories: [unit/integration/e2e]

### Iteration I2
- ...

## 5. Test strategy
- Per iteration: [coverage focus]
- Categories: [unit/integration/e2e]

## 6. Feature flags & migrations
- Flags: [name / behavior]
- Migrations: [what/where]

## 7. Observability
- Logs/metrics/alerts: [what we add or update]

## 8. Risks
- [risk] → [mitigation]

## 9. Open questions
- [question] → [owner] → [due date]

## Plan Review
Status: PENDING
Note: Action items must live under `### Action items`. Avoid checkboxes elsewhere in the Plan Review section.

### Summary
- [short takeaways]

### Findings
- [severity] [issue] — [recommendation]

### Action items
- None
- <action> — <owner> — <due date>
