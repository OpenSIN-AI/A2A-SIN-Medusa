# A2A-SIN-Medusa — AGENTS.md

## Purpose

The Self-Extender Agent (Software 3.0). Operating within the Team-SIN-FlowFactory ecosystem.

## Rules

- NEVER ask user for manual help — find your own way
- ALWAYS use opencode CLI for LLM calls — never direct API calls
- ALWAYS publish logs and evidence to the approved artifact storage surface — never leave critical artifacts only on the local machine
- ALWAYS follow the Google account matrix for any Google operations
- ALWAYS use the approved OpenSIN browser automation surfaces — never ad-hoc raw automation

## Development Guidelines
- Use `opencode` CLI for all LLM interactions
- Follow the Global Brain PCPM integration
- All changes must be committed via pull requests
- Run tests before pushing

## Quick Start
```bash
git clone https://github.com/OpenSIN-AI/A2A-SIN-Medusa.git
cd A2A-SIN-Medusa
bun install
bun run build
bun start
```

## Boundary Guidance for Agents

When modifying this repo:

- Prefer Medusa synthesis loops and autonomous tool generation work.
- Do not turn this repo into a generic tool bucket.
- Do not redefine organization docs, architecture, or runtime canon here.
- Move non-synthesis behavior back to the repos that own those surfaces.

## License

Apache-2.0
