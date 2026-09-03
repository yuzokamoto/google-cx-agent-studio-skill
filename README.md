# Google CX Agent Studio Skill

A focused engineering skill for designing, implementing, reviewing, debugging, securing, evaluating, versioning, and deploying applications built with **Google Cloud Customer Experience Agent Studio (CX Agent Studio)**.

This repository is intentionally generic across industries, but deliberately **specific to CX Agent Studio** rather than to conversational AI or Google Cloud as a whole.

## Scope

Use this skill when CX Agent Studio is the primary subject or a material integration/migration target, including:

- building or reviewing a CX Agent Studio application;
- configuring its agents, tools, state, callbacks, handoffs, guardrails, knowledge, evaluations, versions, or deployment channels;
- integrating CX Agent Studio with external APIs, MCP servers, knowledge sources, or supported channels/platforms;
- integrating/migrating Dialogflow CX flows into or with CX Agent Studio;
- automating CX Agent Studio resources through its REST/RPC APIs or official MCP server.

Do **not** use it as the primary skill for standalone Dialogflow CX, generic MCP, generic Google Cloud IAM/networking/security, Agent Assist, or CX Insights work when CX Agent Studio is not materially involved.

## Install

Compatible agent-skill clients can install this repository directly, for example:

```bash
npx skills add yuzokamoto/google-cx-agent-studio-skill
```

## What it covers

- Root agents, sub-agents, descriptions, routing, and deterministic handoff rules
- Agent instructions, XML restructuring, tool/agent/variable references, and language guidance
- OpenAPI, Python, MCP, Client Function, Data Store, File Search, Google Search, connectors, system/widget tools, and agent-as-a-tool
- CX Agent Studio Python runtime details for executable Python tools/callbacks, including runtime globals, supported imports, callback signatures, tool-to-tool calls, and networking limits
- Synchronous versus asynchronous tool execution
- Static and dynamic variables, session context injection, callbacks, and deterministic control
- Fallback behavior, retries, tool/integration failures, business-negative outcomes, and escalation/end-session boundaries
- Knowledge grounding and the boundary between RAG and authoritative transactional data
- Prompt Guard, blocklists, safety, rules, logging/redaction, authentication, networking, and security boundaries
- Golden and scenario evaluations, expectations, Simulator traces, and regression workflows
- Versions, export/import, Git workflows, environment-specific configuration, Web/API/platform deployment, and traffic splitting
- Dialogflow CX flow-based agents and migration considerations **as they relate to CX Agent Studio**
- CX Agent Studio REST/RPC APIs and official MCP server for administration/automation

## Repository security model

This public repository is also an instruction supply-chain surface: AI coding agents may read `SKILL.md`, repository documentation, issues, pull requests, comments, and external sources. The repository therefore treats public contributor content as **untrusted data**, not as authorization.

Security controls include:

- `AGENTS.md` as the canonical agent trust-boundary policy, with companion instructions for Claude Code and GitHub Copilot;
- CODEOWNERS coverage for the whole repository and explicit ownership of agent/security-critical files;
- a deterministic PR security gate that inspects the complete pull-request head through the GitHub API **without executing contributor-controlled code**;
- a text-only repository allowlist that rejects unexpected file types, binaries, symlinks, submodules, executable files, and oversized files;
- rejection of invisible/bidirectional Unicode and hidden/active Markdown HTML on agent-consumed documentation;
- workflow enforcement for explicit read-only permissions, no repository/environment secrets, no self-hosted runners, no direct GitHub-expression interpolation inside shell commands, and no privileged untrusted-content event workflows;
- GitHub Actions pinned to full commit SHAs rather than mutable tags;
- Dependabot updates for pinned GitHub Actions;
- existing skill integrity/freshness checks plus the repository security scanner.

These controls reduce attack surface but cannot prove that arbitrary natural-language text is semantically safe. Human/code-owner review remains required for changes to agent instructions and security policy. See `SECURITY.md`, `CONTRIBUTING.md`, and `AGENTS.md`.

## Structure

```text
google-cx-agent-studio-skill/
├── AGENTS.md
├── CLAUDE.md
├── CONTRIBUTING.md
├── SECURITY.md
├── SKILL.md
├── scripts/
│   ├── check_repository_security.py
│   └── check_skill_integrity.py
└── references/
    ├── source-policy.md
    ├── agents-and-handoffs.md
    ├── instructions.md
    ├── tools.md
    ├── python-runtime.md
    ├── knowledge-grounding.md
    ├── state-callbacks-determinism.md
    ├── error-handling.md
    ├── security-and-guardrails.md
    ├── evaluations-debugging.md
    ├── versioning-deployment.md
    ├── flows-and-migration.md
    └── api-and-automation.md
```

The main skill routes the agent to only the references needed for the task, avoiding unnecessary context loading.

## Design principles

1. Official Google Cloud documentation is the product source of truth for platform behavior, using the source appropriate to the type of claim.
2. Runtime behavior is verified from Simulator traces, API responses, or exported configuration instead of guessed.
3. Deterministic requirements are enforced by the layer that owns the responsibility.
4. Agents receive the minimum useful context and tool surface.
5. RAG is not treated as a transactional system of record.
6. Evaluations are part of implementation, not an optional final step.
7. Versions and exports provide rollback/review boundaries; Git provides collaborative source history.

## Platform snapshot used for this audit

This version was reviewed on **2026-09-03** against the current CX Agent Studio documentation and release notes available at that date.

Dated CX Agent Studio release notes explicitly establish these post-March-2026 additions:

- static and dynamic variables — April 13;
- synchronous and asynchronous tool execution — April 17;
- agent-as-a-tool — April 17;
- configurable fallback behavior — April 20;
- custom HTTP headers for MCP tools — May 8;
- Google Maps, Confluence, Jira, and SharePoint tools — May 26;
- evaluation import/export — June 8;
- deployment traffic splitting — July 1.

The current platform also documents capabilities that were absent from, or not covered by, the March 2026 baseline used as inspiration, including current export/import environment handling and the official CX Agent Studio MCP server. This wording does **not** claim a post-March release date where the release notes used for this audit do not establish one.

Because CX Agent Studio changes quickly, the skill instructs agents to re-check official docs and release notes for time-sensitive claims. Repository integrity/freshness checks make an aging audit snapshot visible, but they do not auto-update product facts.

## Product boundaries

Do not treat these names as synonyms:

- **CX Agent Studio** — the generative, agent-oriented application builder covered by this skill.
- **Dialogflow CX** — a flow/page/intent-oriented conversational platform that is in scope here only when integrating/migrating with CX Agent Studio.
- **Agent Assist** — capabilities for assisting human agents; in scope here only when the CX Agent Studio boundary/integration is the question.
- **CX Insights** — contact-center conversation analytics/insights; in scope here only when the CX Agent Studio boundary/integration is the question.

## Sources

Primary documentation:

- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/python
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export

See `references/source-policy.md` for claim-type evidence routing and freshness rules.

## Maintenance

The repository includes deterministic integrity and security checks. The integrity checker validates the skill frontmatter, routed reference files, and audit-age threshold. The security checker validates the repository shape and high-risk supply-chain invariants. A scheduled workflow also probes official Google Cloud documentation links and treats transient network/service failures as warnings rather than rewriting or silently invalidating product content.

The checks are intentionally conservative: a stale snapshot, broken reference, or expanded attack surface should trigger human review, not an automated documentation rewrite.

## Acknowledgement

The initial scope was audited against the public [Yash-Kavaiya/cx-agent-studio-skill](https://github.com/Yash-Kavaiya/cx-agent-studio-skill) repository, whose README stated a March 2026 documentation sync. This repository is independently rewritten, reorganized, and updated rather than reproducing that skill textually.

## License

MIT. See `LICENSE`.
