# Solidify Rubric

Use this reference when hardening a prompt. Keep it operational and do not quote it verbatim to the user.

## Risk Signals

Increase risk when the draft prompt includes:

- broad verbs such as `build`, `refactor`, `productionize`, `optimize`, `clean up`, or `fix everything`
- vague success language such as `make it better`, `make it scalable`, or `production ready`
- no clear acceptance criteria
- no explicit constraints
- no non-goals
- sensitive surfaces such as auth, schema, payments, deployment, or policy compliance
- repo-wide scope language
- requests that imply long-running autonomous execution
- prompts that modify an existing codebase without saying how the change should fit current architecture, interfaces, conventions, or tests

Treat prompt length as a weak signal only. A short prompt can still be high risk.

## Question Categories

Generate questions only from categories that could materially change execution:

1. Objective
2. Scope
3. Constraints
4. Acceptance criteria
5. Environment
6. Decision authority
7. Edge cases
8. Existing codebase integration
9. Output preference
10. Stop conditions

## Priority Formula

Use:

`priority = execution_impact * ambiguity * irreversibility * non_inferability`

Use 1 to 5 scales for:

- `execution_impact`: how much the answer changes the agent's work
- `ambiguity`: how unclear the draft prompt is on this point
- `irreversibility`: how costly a wrong assumption would be
- `non_inferability`: how hard it is to answer safely from repo context

Downgrade questions that are:

- cosmetic
- redundant
- already answered indirectly
- safe to cover with a conservative default

## Default Patterns

Prefer conservative defaults such as:

- smallest file scope that can solve the task
- no unrelated refactors
- no new dependencies unless clearly justified
- no deployment or infrastructure changes unless requested
- ask before changing schema, auth model, billing flow, or public APIs
- preserve existing architecture, interfaces, naming, and conventions unless a change is explicitly requested
- concise deliverables with explicit acceptance criteria

## Existing Codebase Integration Cues

When the prompt adds to or changes an existing codebase, first inspect the local implementation and use it to resolve baseline questions.

Ask integration-specific questions only when the repo does not already answer them, such as:

- which existing modules or entrypoints should own the change
- whether public interfaces or database shapes must remain backward compatible
- whether current tests describe the intended behavior
- whether the change should follow an existing pattern nearby or introduce a new abstraction
- what parts of the codebase are explicitly out of scope

## Weak Prompt Example

`Implement auth for this app and make it production ready.`

Likely missing:

- allowed auth methods
- scope boundaries
- dependency policy
- what `production ready` means
- what the agent must not touch

## Hardened Prompt Shape

A good production-ready prompt should make these explicit:

- the exact objective
- known repo context
- scope and non-goals
- constraints
- acceptance criteria
- how the change should fit into the existing codebase
- allowed assumptions
- disallowed assumptions
- escalation rules
- deliverable format
