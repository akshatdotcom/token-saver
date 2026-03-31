# Solidify

A prompt-hardening skill for Claude Code that turns vague agent prompts into production-ready specs.

Run `/solidify [draft prompt]` before sending a task to an agent. It analyzes risk, asks ranked clarification questions, and compiles a hardened prompt with explicit assumptions, stop conditions, and a structured JSON session artifact.

## What it does

1. Reads your draft prompt and lightweight repo context
2. Identifies high-risk gaps and missing constraints
3. Asks 3-12 ranked questions (fewest needed, smart defaults for skipping)
4. Outputs a production-ready prompt, assumption ledger, remaining risks, and machine-readable session JSON

## Install

Copy `.claude/skills/solidify/` into your project's `.claude/skills/` directory.

## Usage

```
/solidify Implement auth for this app and make it production ready
```

## License

MIT
