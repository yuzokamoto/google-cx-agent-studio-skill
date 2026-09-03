# Source Policy and Product Freshness

CX Agent Studio evolves quickly. Treat product behavior as time-sensitive unless it is a stable architectural principle.

## Source hierarchy

Use sources in this order when resolving product facts:

1. **Current Google Cloud CX Agent Studio documentation** under `docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio`.
2. **CX Agent Studio release notes** for recent features, changes, deprecations, and launch-stage changes.
3. **CX Agent Studio REST/RPC reference** for exact resource schemas, enums, fields, default values, and API behavior.
4. **Observed runtime evidence** from Simulator traces, tool tests, exported application configuration, or API responses.
5. **Official Google Cloud samples and community/forum posts** for examples and operational troubleshooting.
6. Third-party repositories or discussions only as secondary evidence.

If two sources conflict, prefer the newer official product/API documentation and call out the conflict when material.

## Facts that require freshness verification

Re-check current documentation for:

- available tool types and connector integrations;
- model IDs, defaults, and deprecations;
- GA versus Preview/Pre-GA status;
- supported regions and language/channel limitations;
- tool timeout/default execution behavior;
- Web Widget authentication and security behavior;
- REST `v1` versus `v1beta` resource availability;
- export/import format and environment dependencies;
- evaluation features and metrics;
- deployment and traffic-splitting capabilities;
- MCP transport/authentication requirements;
- quotas, limits, billing, and pricing.

Do not encode these as eternal truths in generated architecture.

## Evidence labels

When a distinction matters, use one of these labels in analysis/reviews:

- **Documented:** directly supported by current official documentation.
- **Observed:** established from a trace/export/API response supplied or inspected for the application.
- **Recommended:** architecture or engineering guidance, not a platform guarantee.
- **Unverified:** plausible but not established from an authoritative/current source.

Do not convert `Unverified` into a firm answer.

## Runtime verification rule

Documentation often describes callback signatures and conceptual tool behavior but may not establish the exact wrapper seen in a particular execution path. Before writing production callback code that depends on exact runtime structures:

1. test the tool directly;
2. reproduce through Preview/Simulator;
3. inspect Steps/trace;
4. capture the runtime tool name, input shape, response shape, and variable updates;
5. implement against the observed shape;
6. add an evaluation that protects the behavior.

## Product boundaries

Keep these products/capabilities separate unless official documentation explicitly connects them:

### CX Agent Studio
Agent-oriented application builder with instructions, tools, variables, callbacks, handoffs, guardrails, evaluations, versions, and deployment channels.

### Dialogflow CX
Flow/page/intent-based conversational platform. Existing flows can be imported as flow-based agents into CX Agent Studio with explicit variable mappings.

### Agent Assist
Human-agent assistance product/capabilities. Do not assume an Agent Assist feature is available to a CX Agent Studio autonomous agent.

### CX Insights
Conversation analytics/insights product. Do not assume CX Insights is a built-in CX Agent Studio feature merely because both belong to the broader customer-experience portfolio.

## Current audit baseline

This repository was audited on **2026-09-03**. The CX Agent Studio release-notes page available at that time was last updated 2026-08-26 and listed production feature entries through 2026-07-01.

Notable post-March-2026 changes incorporated here include:

- static and dynamic variables (April 13);
- agent-as-a-tool and sync/async tool execution (April 17);
- configurable fallback behavior (April 20);
- MCP custom headers (May 8);
- Maps, Confluence, Jira, and SharePoint tools (May 26);
- evaluation import/export (June 8);
- deployment traffic splitting (July 1).

This list is a historical baseline, not a substitute for checking future release notes.

## Canonical links

- Overview: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio
- Release notes: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
- Best practices: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices
- REST reference: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest
- RPC reference: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1
- Export format: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export
