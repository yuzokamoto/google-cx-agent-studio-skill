# Source Policy and Product Freshness

CX Agent Studio evolves quickly. Treat product behavior as time-sensitive unless it is a stable architectural principle.

## Choose evidence by claim type

Do not use a single universal source ranking. Different sources are authoritative for different questions.

| Claim type | Preferred evidence | Notes |
|---|---|---|
| Supported capability, console behavior, setup workflow | Current CX Agent Studio product documentation | Re-check launch stage and page update date when material. |
| Release chronology, deprecation announcement, GA/Preview transition | CX Agent Studio release notes plus current product documentation | A dated release note supports chronology; current docs establish present behavior. |
| Exact REST/RPC resource field, enum, default, method, or API version | Current versioned REST/RPC reference | Do not mix `v1` and `v1beta` schemas. |
| What actually happened in a specific application/session | Simulator trace, Tool Test, exported configuration, or API response | Treat as **Observed** evidence for that app/runtime, not a universal platform guarantee. |
| Recommended architecture or engineering pattern | Current official best-practices/security/networking documentation plus clearly labeled engineering judgment | Recommendations are not product guarantees. |
| Troubleshooting hypothesis or undocumented operational workaround | Official sample/community/forum evidence, then independently verify against runtime or current docs | Community evidence is secondary and should not become a product contract by repetition. |

If sources conflict, first identify **what kind of claim is being resolved**. Prefer the current source authoritative for that claim type, and call out material conflicts rather than silently reconciling them.

## Official and secondary evidence boundaries

Use official Google Cloud sources for platform contracts whenever they exist:

- CX Agent Studio product documentation;
- release notes;
- REST/RPC/MCP references;
- official best-practice, security, networking, and deployment documentation;
- official samples when they illustrate supported patterns.

Community/forum posts and third-party repositories are useful for discovering failure modes, examples, and hypotheses. They are not authoritative for supported capabilities, API schemas, security guarantees, limits, or launch stage unless independently confirmed.

## Facts that require freshness verification

Re-check current documentation for:

- available tool types and connector integrations;
- model IDs, defaults, and deprecations;
- GA versus Preview/Pre-GA status;
- supported regions and language/channel limitations;
- tool timeout/default execution behavior;
- networking/private-connectivity support;
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

- **Documented:** directly supported by current official documentation appropriate to the claim type.
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

The following post-March-2026 changes are explicitly supported by dated CX Agent Studio release notes:

- static and dynamic variables — April 13;
- agent-as-a-tool and synchronous/asynchronous tool execution — April 17;
- configurable fallback behavior — April 20;
- MCP custom headers — May 8;
- Google Maps, Confluence, Jira, and SharePoint tools — May 26;
- evaluation import/export — June 8;
- deployment traffic splitting — July 1.

Other capabilities documented by the current platform but not established by those release-note entries should be described as **present in the current platform and absent from, or not covered by, the March 2026 baseline** rather than claimed to have been added after March.

This list is a historical audit baseline, not a substitute for checking future release notes.

## Repository freshness checks

The repository includes lightweight integrity checks intended to make staleness visible without automatically rewriting product facts.

They should verify:

- `SKILL.md` has the expected basic frontmatter;
- reference files routed from `SKILL.md` exist;
- the audit snapshot has not exceeded the configured review-age threshold;
- canonical official documentation links are not known-broken;
- link/network failures that do not prove a broken URL are surfaced as warnings rather than silently changing content.

A failed freshness check means **human review is required**. CI must not infer a new product truth from release notes and rewrite the skill automatically.

## Canonical links

- Overview: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio
- Release notes: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
- Best practices: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices
- REST reference: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest
- RPC reference: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1
- Export format: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export
