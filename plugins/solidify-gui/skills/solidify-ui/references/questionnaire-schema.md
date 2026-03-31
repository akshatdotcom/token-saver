# Questionnaire Schema

This skill writes two session files under:

`${CLAUDE_PLUGIN_DATA}/sessions/${CLAUDE_SESSION_ID}/`

## `questionnaire.json`

Write this file before launching the browser wizard.

```json
{
  "schemaVersion": 1,
  "sessionId": "string",
  "draftPrompt": "string",
  "workspacePath": "string",
  "riskSummary": ["string"],
  "repoFacts": ["string"],
  "questions": [
    {
      "id": "string",
      "importance": "required | recommended | optional",
      "category": "string",
      "question": "string",
      "whyItMatters": "string",
      "recommendedDefault": "string",
      "assumptionIfSkipped": "string",
      "evidence": ["string"]
    }
  ],
  "outputSections": [
    "Objective",
    "Known Context",
    "Scope",
    "Non-Goals",
    "Constraints",
    "Acceptance Criteria",
    "Allowed Assumptions",
    "Disallowed Assumptions",
    "Escalation Rules",
    "Deliverable Format"
  ]
}
```

## `answers.json`

The browser wizard writes this file after the user submits.

```json
{
  "schemaVersion": 1,
  "responses": [
    {
      "id": "string",
      "mode": "custom | default | skip",
      "value": "string",
      "finalValue": "string"
    }
  ],
  "extraNotes": "string"
}
```

## Validation Rules

- Every question in `questionnaire.json` must have a matching `id`.
- Every response in `answers.json` must map to an existing question id.
- The browser wizard starts each question in `custom` mode.
- `mode=custom` requires a non-empty `value`.
- `mode=default` uses the question’s `recommendedDefault`.
- `mode=skip` uses the question’s `assumptionIfSkipped`.
- Required questions must not remain unresolved when compiling the final production-ready prompt. If a required answer is still missing, record the gap as an unresolved risk and ask the user to fix it.
