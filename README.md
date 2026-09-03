# Google CX Agent Studio Skill

A focused engineering skill for designing, implementing, reviewing, debugging, securing, evaluating, versioning, and deploying applications built with **Google Cloud Customer Experience Agent Studio (CX Agent Studio)**.

This repository is intentionally generic: it contains product-oriented guidance and decision frameworks rather than project-specific business rules.

## Install

Compatible agent-skill clients can install this repository directly, for example:

```bash
npx skills add yuzokamoto/google-cx-agent-studio-skill
```

## What it covers

- Root agents, sub-agents, descriptions, routing, and deterministic handoff rules
- Agent instructions, XML restructuring, tool/agent/variable references, and language guidance
- OpenAPI, Python, MCP, Client Function, Data Store, File Search, Google Search, connectors, system/widget tools, and agent-as-a-tool
- Synchronous versus asynchronous tool execution
- Static and dynamic variables, session context injection, callbacks, and deterministic control
- Knowledge grounding and the boundary between RAG and authoritative transactional data
- Prompt Guard, blocklists, safety, rules, logging/redaction, authentication, and security boundaries
- Golden and scenario evaluations, expectations, Simulator traces, and regression workflows
- Versions, export/import, Git workflows, environment-specific configuration, Web Widget deployment, and traffic splitting
- Dialogflow CX flow-based agents and migration considerations
- REST API and the official CX Agent Studio MCP server for administration/automation

## Structure

```text
google-cx-agent-studio-skill/
├── SKILL.md
└── references/
    ├── source-policy.md
    ├── agents-and-handoffs.md
    ├── instructions.md
    ├── tools.md
    ├── knowledge-grounding.md
    ├── state-callbacks-determinism.md
    ├── security-and-guardrails.md
    ├── evaluations-debugging.md
    ├── versioning-deployment.md
    ├── flows-and-migration.md
    └── api-and-automation.md
```

The main skill routes the agent to only the references needed for the task, avoiding unnecessary context loading.

## Design principles

1. Official Google Cloud documentation is the product source of truth.
2. Runtime behavior is verified from Simulator traces, API responses, or exported configuration instead of guessed.
3. Deterministic requirements are enforced in deterministic layers.
4. Agents receive the minimum useful context and tool surface.
5. RAG is not treated as a transactional system of record.
6. Evaluations are part of implementation, not an optional final step.
7. Versions and exports provide rollback/review boundaries; Git provides collaborative source history.

## Platform snapshot used for this audit

This version was reviewed on **2026-09-03** against the current CX Agent Studio documentation and release notes available at that date. Notable capabilities added after the March 2026 baseline used as inspiration include:

- static and dynamic variables;
- synchronous and asynchronous tool execution;
- agent-as-a-tool;
- custom HTTP headers for MCP tools;
- Google Maps, Confluence, Jira, and SharePoint tools;
- evaluation import/export;
- deployment traffic splitting;
- application/tool export-import improvements and environment-specific dependencies;
- the official CX Agent Studio MCP server for programmatic administration.

Because CX Agent Studio changes quickly, the skill instructs agents to re-check official docs and release notes for time-sensitive claims.

## Product boundaries

Do not treat these names as synonyms:

- **CX Agent Studio** — the generative, agent-oriented application builder covered by this skill.
- **Dialogflow CX** — a flow/page/intent-oriented conversational platform that can be integrated through flow-based agents.
- **Agent Assist** — capabilities for assisting human agents; related to Google Cloud contact-center products but not equivalent to CX Agent Studio.
- **CX Insights** — contact-center conversation analytics/insights; related but distinct from CX Agent Studio.

## Sources

Primary documentation:

- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export

See `references/source-policy.md` for the source hierarchy used by the skill.

## Acknowledgement

The initial scope was audited against the public [Yash-Kavaiya/cx-agent-studio-skill](https://github.com/Yash-Kavaiya/cx-agent-studio-skill) repository, whose README stated a March 2026 documentation sync. This repository is independently rewritten, reorganized, and updated rather than reproducing that skill textually.

## License

MIT. See `LICENSE`.
