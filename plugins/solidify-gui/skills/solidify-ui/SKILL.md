---
name: solidify-ui
description: Make your prompt production-ready before you let the agent cook, using a local browser wizard instead of a chat-only flow. Use when a coding or agent prompt is broad, ambiguous, or high-cost and the user wants a GUI-guided hardening pass.
disable-model-invocation: true
---

# Solidify UI

Use this skill to run the `solidify` hardening workflow through a localhost browser wizard instead of asking every clarification question inline in chat.

This skill is still preflight only:

- Do not edit the user’s code or start implementation while the hardening flow is active.
- Stop after producing the production-ready prompt, assumption ledger, and remaining risks.
- If the browser launch fails or the user does not want the GUI, fall back to the normal chat-based hardening flow.

## Inputs

- Draft prompt: `$ARGUMENTS`
- Current repo context and existing codebase shape
- Relevant project files that answer baseline questions about the requested change

If `$ARGUMENTS` is empty, ask the user to paste the draft prompt before doing anything else.

## References

Before creating the questionnaire:

- Read [references/rubric.md](references/rubric.md) for risk scoring, prioritization, and default policy.
- Read [references/questionnaire-schema.md](references/questionnaire-schema.md) for the exact JSON files this skill must write and later read back.

## Workflow

1. Inspect the repo using read-only actions first.
2. Resolve any obvious baseline facts from the existing codebase before asking the user.
3. Build:
   - a short risk summary
   - repo facts that materially constrain implementation
   - a ranked question set
4. Write `questionnaire.json` to:
   - `${CLAUDE_PLUGIN_DATA}/sessions/${CLAUDE_SESSION_ID}/questionnaire.json`
5. Launch the local browser wizard with:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/launch_wizard.py" \
  --session-dir "${CLAUDE_PLUGIN_DATA}/sessions/${CLAUDE_SESSION_ID}"
```

6. Tell the user the wizard should be open in their browser and instruct them to finish it, then reply `done`.
7. When the user replies `done`, read:
   - `${CLAUDE_PLUGIN_DATA}/sessions/${CLAUDE_SESSION_ID}/answers.json`
8. Compile the final production-ready prompt output from the questionnaire plus the saved answers.

## Repo-Aware Rules

- Prefer questions about integration into the current codebase over abstract questions.
- Use nearby code, tests, interfaces, routes, schemas, and naming patterns to answer baseline questions before asking the user.
- Ask about compatibility, boundaries, touched surfaces, and desired fit with current architecture only when the repo does not already answer them.

## Question Policy

- Ask the fewest questions that materially reduce execution risk.
- Use the same risk-based question budget as the chat skill:
  - Low risk: 3 to 5
  - Medium risk: 5 to 8
  - High risk: 8 to 12
- Every question in `questionnaire.json` must include:
  - `id`
  - `importance`
  - `category`
  - `question`
  - `whyItMatters`
  - `recommendedDefault`
  - `assumptionIfSkipped`
  - `evidence`

## Before Launching The Wizard

Your last chat message before launch should be short and should include:

- a 2 to 4 bullet risk summary
- how many questions are in the wizard
- a note that the browser wizard is opening
- an instruction to reply `done` after submitting the wizard

Do not dump the full questionnaire in chat unless the user asks for it.

## After The User Replies `done`

1. Read `answers.json`.
2. Validate that every required question has either:
   - a custom answer
   - an accepted default
   - or an explicitly recorded unresolved risk
3. If `answers.json` is missing or incomplete, explain what is missing and ask the user to finish the wizard.
4. If it is complete, produce:

~~~md
## Production-Ready Prompt
```md
# Objective

# Known Context

# Scope

# Non-Goals

# Constraints

# Acceptance Criteria

# Allowed Assumptions

# Disallowed Assumptions

# Escalation Rules

# Deliverable Format
```

## Assumption Ledger
- User answer: ...
- Default accepted: ...
- Skipped with assumption: ...
- Unresolved: ...

## Remaining Risks
- ...
- ...
~~~

Stop after this output. Do not proceed into execution automatically.
