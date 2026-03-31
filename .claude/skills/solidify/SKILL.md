---
name: solidify
description: Make your prompt production-ready before you let the agent cook. Use when a coding or agent prompt is broad, high-cost, ambiguous, or likely to hide assumptions, and the user wants ranked clarification questions plus a production-ready prompt spec.
argument-hint: "[draft prompt]"
disable-model-invocation: true
---

# Solidify

Use this skill to turn a draft prompt into a production-ready prompt spec before any implementation work starts.

This skill is preflight only:

- Do not edit files, run mutating commands, or start implementing the task while the hardening flow is active.
- Do not continue automatically into execution after the prompt is production-ready.
- Stop after producing the production-ready prompt, assumption ledger, remaining risks, and session JSON.

## Inputs

- Draft prompt: `$ARGUMENTS`
- Current repo context and existing codebase shape
- Local docs, specs, READMEs, or other relevant project files when they are clearly relevant

If `$ARGUMENTS` is empty, ask the user to paste the draft prompt before doing anything else.

## Supporting Reference

Before scoring risks or drafting questions, read [references/rubric.md](references/rubric.md). Use it as the source of truth for:

- risk signals
- question categories
- prioritization
- conservative defaults
- existing-codebase integration cues

## Operating Rules

- First inspect the repo with read-only actions only.
- Read only high-signal files unless a deeper read is needed to resolve a specific ambiguity.
- Treat repo facts as truth when they are clear.
- Never ask a question that can be answered safely from repo context.
- If the prompt is about adding to, changing, or extending an existing codebase, use the current implementation to answer baseline questions before asking the user.
- When relevant, prefer integration questions over abstract questions. Ask about compatibility, boundaries, touched surfaces, and expected behavior relative to existing code.
- Optimize for general developer workflows by default.
- Keep the process efficient: ask the fewest questions that materially reduce execution risk.

## Exploration Pass

Before asking any clarification questions:

1. Capture the draft prompt.
2. Inspect the repo at a lightweight level.
3. Read only the highest-signal files that are likely to answer basic context questions.

Prioritize:

- root directory listing
- README and top-level docs
- package manifests and lockfiles
- framework or runtime config files
- adjacent files and modules near the requested change
- existing public interfaces, routes, schemas, or APIs that the change would need to fit
- test files
- explicit spec files if they are obvious

Do not do a deep codebase crawl unless a specific high-impact ambiguity requires it.

## Internal Analysis

Build an internal model with:

- known facts from the prompt
- known facts from the repo
- risky phrases such as "production ready", "optimize", "refactor", "fix everything", or "make it scalable"
- missing constraints
- hidden assumptions the agent would otherwise make
- sensitive areas like auth, schema, payments, deployment, or policy compliance
- existing code paths, conventions, or tests that constrain how the change should fit into the codebase

## Question Generation

Generate candidate questions across these categories:

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

Score each candidate question using the rubric reference. Prefer questions whose answers would materially change what the agent does.

Deduplicate aggressively. Drop questions that are:

- already answered by the prompt
- clearly inferable from the repo
- cosmetic
- redundant with a higher-priority question

## Question Budget

Set the question budget from the overall risk level:

- Low risk: target 3 to 5 questions
- Medium risk: target 5 to 8 questions
- High risk: target 8 to 12 questions

You may stop before the top of the budget if the remaining questions are low value or redundant.

## First Response

Your first reply should contain:

1. A short risk summary, 2 to 4 bullets max
2. The planned question count for this hardening run
3. The first clarification question

Use this format:

```md
## Risk Summary
- ...
- ...

I plan to ask up to N clarification questions, one at a time.

## Clarification 1 of N
Importance: Required | Recommended | Optional
Why it matters: ...
Recommended default: ...
Assumption if skipped: ...
Question: ...
```

## Asking Questions

Ask one clarification question at a time.

For each question:

- mark it as `Required`, `Recommended`, or `Optional`
- explain briefly why it matters
- give a conservative recommended default
- say what assumption will be recorded if the user skips it

After asking a question, stop and wait for the user.

When the user responds:

- If they answer directly, record the answer and continue.
- If they say `default`, `use default`, or clearly accept the default, record the recommended default and continue.
- If they say `skip` and the question is not required, record the skip and continue.
- If they skip a required question, explain briefly why it is required and ask once more. If the user still refuses, choose the smallest safe default and record it as an unresolved risk.
- If the answer resolves later questions, collapse those questions and reduce the remaining count.
- If the answer is partial but useful, ask only the smallest follow-up needed.

## Session Tracking

Throughout the hardening flow, track the following for the Session JSON artifact:

- **original_prompt**: capture from `$ARGUMENTS` at the start
- **repo_facts**: collect file paths read during the exploration pass
- **clarifications**: after each question is resolved, record it as an object with `id` (snake_case slug from category and topic, e.g. `scope_edit_breadth`), `category`, `importance`, `prompt`, `recommended_default`, `answer` (the actual value used), and `disposition` (`answered` if the user gave a direct answer, `default_accepted` if they accepted the default, `skipped` if they skipped)
- **risk_level**: the assessed level from the risk summary (`low`, `medium`, or `high`)
- **question_budget**: the planned question count

Emit the assembled JSON in the `## Session JSON` section at the end of the final output.

## Defaults

Defaults must be conservative and execution-safe.

Prefer defaults like:

- narrow file scope
- no unrelated refactors
- no new dependencies unless clearly justified
- no deployment, billing, auth-model, or schema changes without confirmation
- concise deliverables with explicit acceptance criteria
- pause and ask before making irreversible decisions

Also prefer defaults that preserve existing architecture, naming, tests, interfaces, and local conventions unless the user explicitly wants to change them.

## Production-Ready Prompt Output

Once enough ambiguity has been removed, produce the final output in this structure:

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

## Session JSON
```json
{
  "metadata": {
    "version": "1.0",
    "timestamp": "<ISO 8601>",
    "risk_level": "<low | medium | high>",
    "question_budget": <number>
  },
  "original_prompt": "<draft prompt as a single string>",
  "repo_facts": ["<file paths inspected during exploration>"],
  "clarifications": [
    {
      "id": "<snake_case slug, e.g. scope_edit_breadth>",
      "category": "<question category>",
      "importance": "<required | recommended | optional>",
      "prompt": "<the question asked>",
      "recommended_default": "<the default offered>",
      "answer": "<user's answer or the default value>",
      "disposition": "<answered | default_accepted | skipped>"
    }
  ],
  "unresolved_risks": ["<remaining risk strings>"],
  "final_prompt": "<production-ready prompt as a single string>"
}
```
~~~

Keep the production-ready prompt concrete and easy to paste into the next task turn.

## Final Behavior

After you emit the production-ready prompt and session JSON:

- do not implement the task
- do not start planning the implementation
- do not ask for permission to proceed automatically
- stop with a short note telling the user this production-ready prompt is ready to use in the next Claude task turn

## Quality Bar

The skill is successful when the user feels:

- "It asked things I had not thought about."
- "It did not waste my time on obvious questions."
- "The production-ready prompt is safer and clearer than my original one."
