# Solidify UI Rubric

Use this reference when building a GUI questionnaire for prompt hardening.

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

Treat prompt length as a weak signal only.

## Question Categories

Use only categories that could materially change execution:

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

Favor questions with the highest impact on what the agent will do.

## Conservative Defaults

Prefer defaults such as:

- smallest file scope that can solve the task
- no unrelated refactors
- no new dependencies unless clearly justified
- no deployment or infrastructure changes unless requested
- ask before changing schema, auth model, billing flow, or public APIs
- preserve existing architecture, interfaces, naming, and conventions unless a change is explicitly requested
- concise deliverables with explicit acceptance criteria

## Existing Codebase Integration

When the prompt changes an existing system:

- inspect the implementation first
- inspect nearby tests and interfaces
- prefer integration questions over generic questions
- ask only when the repo does not answer the question safely
