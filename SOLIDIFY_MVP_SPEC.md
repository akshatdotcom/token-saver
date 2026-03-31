# Solidify MVP Spec

## Summary

`solidify` is a prompt hardening tool for long-running agent tasks.

It analyzes a draft prompt before execution, finds the highest-risk gaps, asks the user a short ranked set of clarification questions, and compiles a hardened final prompt that reduces bad assumptions, wasted tokens, and failed agent runs.

The first implementation should work as:

- A manual Claude Code skill invoked as `/solidify`
- A standalone CLI invoked as `solidify`

The core value is not "ask more questions." The core value is:

- Ask only questions that materially change execution
- Order them from highest risk to lowest risk
- Provide smart defaults when skipping is safe
- Produce a final prompt with explicit assumptions and stop conditions

## Problem

Long agent prompts often contain hidden ambiguity.

Typical failure modes:

- The agent assumes the wrong scope
- The agent optimizes for the wrong success criteria
- The agent violates hidden constraints in the repo or spec
- The agent edits too broadly because non-goals were omitted
- The agent makes irreversible decisions without checking
- The user burns tokens discovering missing context mid-run

These failures are especially painful for anyone with a limited token budget because ambiguity wastes expensive downstream turns.

## Product Thesis

If agent frameworks are orchestration layers, `solidify` is the preflight layer.

It should sit between the user's draft prompt and the agent's execution. Its job is to turn an underspecified request into an execution-ready spec.

## Target Users

- Hackathon teams moving fast with AI agents
- Solo builders running long agent workflows
- Startup teams that want fewer expensive agent failures
- Developers trying to use tokens efficiently across repeated long runs

## Jobs To Be Done

- "Before I send this to an agent, tell me what I forgot."
- "Ask me the important questions first."
- "Use repo context to avoid asking obvious questions."
- "Give me defaults when I do not care."
- "Compile my answers into a prompt that is safer to run."

## Non-Goals For MVP

- Full autonomous project planning
- Arbitrary multi-agent orchestration
- Persistent memory across projects
- Automatic prompt blocking on every submission
- Deep IDE UI work beyond a simple skill or CLI flow

## MVP Scope

V1 ships four capabilities:

1. Prompt analysis
2. Ranked clarification questions
3. Default answer suggestions
4. Hardened prompt compilation

V1 should be manual and explicit. The user chooses to run `/solidify` or `solidify`.

## Core Workflow

1. User writes a draft prompt for a long-running agent task.
2. User runs `/solidify` or `solidify`.
3. `solidify` reads:
   - the draft prompt
   - lightweight repo context
   - optional docs or spec files
4. `solidify` extracts:
   - known facts
   - implied assumptions
   - missing high-risk information
5. `solidify` generates candidate questions.
6. Questions are scored and sorted.
7. User answers, accepts defaults, or skips optional questions.
8. `solidify` emits:
   - a hardened prompt
   - an assumptions list
   - unresolved risks
   - a machine-readable answer record

## User Experience

### Claude Code Skill

Command:

```text
/solidify [optional draft prompt]
```

Behavior:

- If arguments are provided, use them as the draft prompt.
- If no arguments are provided, ask the user to paste the draft prompt.
- Read local repo context using read-only tools.
- Return a ranked questionnaire.
- After answers are collected, output the hardened prompt for the user to send or paste into the next turn.

Recommended skill settings:

- `name: solidify`
- `disable-model-invocation: true`
- `context: fork`
- `agent: general-purpose`

Rationale:

- Manual invocation avoids friction.
- Forked context keeps the hardening process from polluting the main task thread.

### Standalone CLI

Examples:

```bash
solidify prompt.txt
solidify --from-stdin
solidify --prompt "Implement the feature in this repo"
solidify spec.md --repo .
```

Suggested flow:

1. Analyze prompt and repo
2. Show a short risk summary
3. Ask ranked questions one by one
4. Allow:
   - `enter` to accept recommended default
   - `s` to skip optional question
   - `d` to see why the question matters
5. Write outputs to:
   - `solidified-prompt.md`
   - `solidify-session.json`

## Question Design Principles

Questions must be:

- High leverage
- Repo-aware
- Specific
- Action-changing
- Minimal in count

Questions must not be:

- Generic filler
- Easily inferable from local context
- Duplicative
- Low-impact preferences disguised as blockers

## Question Categories

Candidate questions should be generated across these categories:

1. Objective
   - What exact outcome is desired?
2. Scope
   - What is in scope and out of scope?
3. Acceptance criteria
   - How will success be judged?
4. Constraints
   - Dependencies, time, policies, style requirements
5. Environment
   - Runtime, versions, APIs, deployment target, sandbox assumptions
6. Risk tolerance
   - Can the agent refactor broadly or only patch narrowly?
7. Decision authority
   - What can the agent decide alone vs. what requires confirmation?
8. Edge cases
   - What failure scenarios matter most?
9. Output preference
   - Hints vs. full solution, prose vs. code, plan-first vs. implement-first
10. Stop conditions
   - When must the agent pause and ask instead of guessing?

## Ranking Model

Each candidate question gets a score:

```text
priority = execution_impact * ambiguity * irreversibility * non_inferability
```

Suggested 1-5 scales:

- `execution_impact`: how much the answer changes the agent's work
- `ambiguity`: how unclear the current prompt is on this point
- `irreversibility`: how costly a wrong assumption would be
- `non_inferability`: how hard it is to infer safely from repo/spec context

Then downgrade questions that are:

- cosmetic
- redundant with answered questions
- safely defaultable

## Default Answer Strategy

Every question should include one of:

- `required`: user must answer
- `recommended_default`: default can be accepted with enter
- `optional`: safe to skip

Defaults should be conservative.

Examples:

- Scope default: "Limit edits to the smallest set of files required"
- Risk default: "Ask before making schema, auth, billing, or deployment changes"
- Existing-codebase default: "Preserve current architecture and conventions unless the prompt explicitly asks for change"

## Output Format

The final output should contain four sections.

### 1. Production-Ready Prompt

The prompt sent to the agent should be rewritten into a structured format:

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

### 2. Assumption Ledger

A flat list of:

- explicit user answers
- accepted defaults
- unresolved unknowns

### 3. Risk Summary

Short list of remaining risks if the user skipped optional questions.

### 4. Session Record

Machine-readable JSON with:

- original prompt
- extracted facts
- questions asked
- answers given
- defaults accepted
- final prompt

## Example Interaction

Draft prompt:

```text
Implement auth for this app and make it production ready.
```

`solidify` might respond:

1. Required: What does "production ready" mean for this project?
   Recommended default: basic tests, environment config, and documented run steps, but no cloud deployment.

2. Required: Is the agent allowed to add new dependencies?
   Recommended default: no new dependencies unless clearly justified.

3. Recommended: What files or areas are out of scope?
   Recommended default: avoid unrelated refactors and UI changes.

4. Recommended: Should the new auth flow preserve existing route and schema shapes where possible?
   Recommended default: yes, preserve current interfaces unless a change is required.

## Architecture

### V1 Architecture

- Skill or CLI entrypoint
- Read-only repo scanner
- Prompt analyzer
- Question generator
- Priority scorer
- Interactive answer collector
- Prompt compiler
- JSON session writer

### Claude Code Packaging Plan

V1 can ship without a full plugin marketplace package.

Minimal local layout:

```text
.claude/
  skills/
    solidify/
      SKILL.md
      reference.md
      scripts/
```

V2 plugin layout:

```text
solidify/
  .claude-plugin/
    plugin.json
  skills/
    solidify/
      SKILL.md
      reference.md
  hooks/
    hooks.json
  scripts/
    solidify
```

Plugin component roles:

- `skills/solidify/SKILL.md`
  - manual `/solidify` entrypoint
- `scripts/solidify`
  - optional local CLI wrapper
- `hooks/hooks.json`
  - later `UserPromptSubmit` risk detection
- `.claude-plugin/plugin.json`
  - plugin metadata and optional configuration

### Suggested Internal Modules

- `ingest`
  - load prompt, repo metadata, optional docs
- `analyze`
  - extract facts, unknowns, constraints, risky verbs
- `question_bank`
  - reusable question templates by task type
- `score`
  - rank candidate questions
- `interact`
  - collect answers and defaults
- `compile`
  - build hardened prompt and output files

## Data Model

### Question Object

Each question should be representable as structured data:

```json
{
  "id": "scope_edit_breadth",
  "category": "scope",
  "priority": 84,
  "importance": "required",
  "prompt": "Should the agent keep edits narrowly scoped or is broad refactoring allowed?",
  "why_it_matters": "This changes how many files may be touched and whether the agent may restructure code.",
  "recommended_default": "Keep edits narrowly scoped to the minimum required files.",
  "assumption_if_skipped": "The agent will avoid unrelated refactors.",
  "evidence": [
    "Prompt says 'make it production ready' without scope boundaries."
  ]
}
```

### Session Object

```json
{
  "original_prompt": "...",
  "repo_facts": [],
  "questions": [],
  "answers": [],
  "accepted_defaults": [],
  "unresolved_risks": [],
  "final_prompt": "..."
}
```

## Repo-Aware Analysis Rules

The analyzer should inspect lightweight context before asking questions:

- repo structure
- package manager and lockfiles
- framework files
- README or docs
- config files
- spec files if present
- adjacent code near the requested change
- existing tests and public interfaces when the prompt modifies current behavior

Inference rules:

- If a framework is obvious, do not ask what framework is being used.
- If tests already exist, ask whether behavior should align with them.
- If the prompt extends an existing codebase, prefer integration questions about boundaries, compatibility, conventions, and touched surfaces.
- If the prompt contains terms like "production ready," "clean up," or "optimize," force scoping questions because these phrases are ambiguous.

## Heuristics For High-Risk Prompts

Prompts should trigger extra scrutiny when they include:

- broad verbs like "build," "refactor," "productionize," "fix everything"
- vague outcomes like "make it better" or "make it scalable"
- missing acceptance criteria
- no mention of constraints
- no explicit non-goals
- sensitive areas like auth, payments, schema, or deployment
- requests to extend an existing system without saying how the change should fit current architecture or interfaces

## Success Metrics

MVP should be judged on:

- average number of questions asked per session
- percent of users accepting at least one default
- reduction in follow-up clarification turns during downstream agent runs
- reduction in major wrong-assumption failures
- user-rated helpfulness of questions
- user-rated annoyance or friction

The product is winning if users say:

- "It asked things I had not thought about."
- "It did not waste my time with obvious questions."
- "The final prompt was better than what I would have written."

## Rollout Plan

### Phase 1

- Manual `/solidify` skill
- Manual CLI
- Markdown and JSON outputs

### Phase 2

- Claude Code plugin packaging
- Reusable question templates by task type
- Project-level saved defaults

### Phase 3

- `UserPromptSubmit` gating for high-risk prompts
- Optional automatic reminder to harden prompts before long runs

### Phase 4

- MCP-backed structured elicitation UI
- Team policy packs

## Risks

1. Too many questions
   - Mitigation: strict ranking and aggressive deduplication

2. Generic advice syndrome
   - Mitigation: require repo-aware evidence for each question

3. Users skip the tool because of friction
   - Mitigation: manual V1, short question count, strong defaults

4. False confidence from hardened prompts
   - Mitigation: include explicit unresolved risks and stop conditions

## MVP Recommendation

Build V1 as a manual Claude Code skill plus a matching CLI.

That gives the fastest path to a usable product:

- no need to start with hook enforcement
- no need to build a full plugin UI first
- no need to solve auto-triggering perfectly

The bet is simple:

If `solidify` can consistently turn a vague long-run prompt into a production-ready prompt spec with 5-10 high-value questions, it is already useful.

## Proposed Tagline

"Before your agent guesses, make the spec explicit."
