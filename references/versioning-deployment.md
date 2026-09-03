# Versioning, Export/Import, Git, and Deployment

Use this reference for immutable versions, rollback, source-control workflows, environment promotion, deployment-channel selection, Web Widget/API/platform deployment, and traffic splitting.

## Versions

CX Agent Studio versions are immutable snapshots of an agent application.

Current behavior documented by Google includes:

- the Versions pane records configuration changes and diffs;
- a version can be created only when configuration has changed;
- versions can be viewed, deleted, and restored;
- restoring preserves unsaved current work in an automatic system version when needed;
- deployments can point to immutable versions.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/version

## When to create a version

Create a version at meaningful working boundaries, especially:

- after relevant evaluations pass;
- before a risky refactor;
- before production/staging deployment;
- before changing agent hierarchy, tool contracts, or global behavior;
- after fixing an important regression.

Google's best-practices page suggests creating versions often and gives roughly every 10-15 major changes as an example, but treat this as guidance rather than a release-policy requirement.

Use meaningful names and descriptions, for example:

```text
v1.3.0-order-cancellation
v1.3.1-fix-auth-handoff
preprod-2026-09-03
```

## Built-in versions are not Git

CX versions are excellent for runtime snapshots and rollback. Git is better for:

- branch-based development;
- pull-request review;
- code ownership;
- semantic diffs over exported files;
- CI checks;
- linking configuration changes to engineering work.

Use both where engineering governance justifies it.

## Export/import

CX Agent Studio supports exporting/importing applications and individual tools.

Current exported application format includes a structured archive with resources such as:

- `app.yaml`;
- global instruction file;
- agent directories/configuration/instruction files;
- tool/toolset definitions;
- callback code;
- `environment.json` for environment-specific dependencies.

The exact structure evolves. Use the current export-format reference before building automation around paths/fields.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/export
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export

## `environment.json`

Current documentation uses `environment.json` to externalize environment-specific dependencies in exported applications. Examples include service endpoints, service accounts, storage resources, data-store URIs, and RAG resources depending on the exported application.

Prefer environment substitution over manually editing multiple generated files for dev/stage/prod differences.

Never commit secrets to `environment.json` or exported configuration.

## Recommended Git workflow

For a production application:

```text
CX Agent Studio draft
  -> export
  -> normalize/review exported files
  -> Git branch
  -> PR + evaluations/static checks
  -> import/promote to target environment
  -> run target integration checks
  -> create immutable CX version
  -> deploy
```

For teams that author exports locally, invert the first steps as appropriate, but always treat one path as authoritative to avoid uncontrolled bidirectional drift.

## Small change versus large refactor

The official CX Agent Studio MCP-server guidance distinguishes two useful workflows:

- **Direct mutation/API/MCP** for small targeted changes;
- **Export → local edit → import** for large architectural refactors, where reviewing many related file changes protects consistency.

Use the smallest workflow that preserves reviewability.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/mcp-server

## Export review checklist

When reviewing an exported app, inspect:

- agent `displayName` and hierarchy;
- instruction references;
- agent tool/toolset ownership;
- static/dynamic variable declarations;
- callback paths and enabled/disabled state;
- environment placeholders;
- authentication/service-account references;
- data-store/RAG dependencies;
- accidental hard-coded endpoints;
- changes to guardrails/application settings;
- new Preview feature dependencies.

Do not assume object paths from an older export format remain current.

## Deployments

Deploy immutable versions rather than relying on an unreviewed draft state.

Before deployment verify:

- target project/location;
- correct application version;
- intended channel type;
- environment endpoints/authentication;
- evaluations passed;
- real integration smoke tests passed;
- logging/redaction/retention settings reviewed;
- channel authentication configured;
- rollback version identified.

## Deployment channel selection

Do not treat Web Widget as the universal deployment path. Choose the channel from the client/contact-center requirements.

Current CX Agent Studio documentation groups deployment into three broad paths:

1. **Web Widget** — a ready-to-use browser/mobile web component for chat, voice, or supported mixed experiences.
2. **Platform connections** — integrations with supported telephony/contact-center platforms.
3. **API access** — direct session integration for a custom client or backend-controlled channel.

At the 2026-09-03 audit, the deployment overview lists platform connections for AudioCodes, Five9, Google Cloud CCaaS, Google Telephony Platform, and Twilio. Treat the vendor list and channel-specific capabilities as time-sensitive and re-check the deployment overview before architecture or procurement decisions.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy

### Requirement-based selection

| Requirement | Default path to evaluate |
|---|---|
| Fast browser-hosted chat/voice UX with Google's ready-made component | Web Widget |
| Fully custom UI, mobile app, backend-controlled session lifecycle, or custom channel adapter | API access |
| Existing supported contact-center/telephony vendor | Platform connection |
| Existing channel not covered by a supported platform connection | API access or a supported adapter architecture |
| Need rich Web Widget interaction components | Web Widget, subject to current widget/language limitations |
| Need channel-specific voice/telephony controls | Relevant platform connection, then verify that platform's current settings/limitations |

Channel choice should consider:

- end-user identity/authentication model;
- session ownership and resume/reconnect behavior;
- voice/chat/video modality requirements;
- latency and streaming requirements;
- rich-content/UI requirements;
- DTMF/barge-in/telephony requirements where applicable;
- browser versus server-side trust boundary;
- network path and corporate firewall restrictions;
- logging/redaction/data-retention requirements;
- vendor/contact-center operational ownership.

## API access

Use API access when the client experience or session lifecycle should be controlled outside the ready-made widget/platform connector.

Current API-access documentation uses a deployment plus a caller-supplied session ID with `runSession`; production systems should use the currently documented service-account/workload authentication pattern rather than development-user credentials.

Use the API when you need, for example:

- a custom web/mobile UI;
- an application-owned session adapter;
- a backend that mediates end-user access;
- integration with a channel not directly supported as a platform connection;
- custom handling of CX Agent Studio response parts/events.

Do not assume an API deployment removes channel responsibilities. The client/adapter still owns appropriate authentication, reconnect/session ID behavior, rendering, accessibility, error handling, and security.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/api-access
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/authentication

## Platform connections

Use a platform connection when the existing telephony/contact-center stack matches a currently supported CX Agent Studio integration and the documented connector satisfies the required channel behavior.

Do not generalize one vendor's setup to another. Platform integrations can differ in:

- supported modality;
- provisioning/phone-number behavior;
- required vendor-side configuration;
- region/number limitations;
- channel-specific behavior settings;
- adapter ownership and deployment model.

For example, current documentation describes Twilio through a deployable open-source telephony adapter supporting voice, SMS, and RCS, while Google Telephony Platform has its own number-provisioning and regional constraints. Those details are channel-specific, not generic CX Agent Studio guarantees.

Always use the current vendor-specific deployment page for implementation.

## Web Widget

Use Web Widget when the ready-made web component fits the UX, authentication, and browser-security requirements.

Current Web Widget documentation requires requests to Google's backend to be authenticated with short-lived credentials. Supported patterns documented at audit time include Google-hosted/self-hosted token brokers, OAuth2, and a custom authentication API.

Current documented limitation: **rich content responses presently support English only**. Do not base a non-English production UX on rich content without re-checking whether that limitation has changed.

The widget runs as a custom element using Shadow DOM rather than a strict isolated iframe by default. Review same-origin storage and XSS implications in `security-and-guardrails.md`.

Before production:

- choose/authenticate the intended user/service identity model;
- configure IAM least privilege;
- review origin/reCAPTCHA protections where applicable;
- sanitize any custom rich content;
- test browser/network restrictions in the real client environment;
- validate session/logout/token-refresh behavior;
- test the exact configured modality (chat, voice, mixed/video where currently supported);
- verify current language/rich-content limitations.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/web-widget

## Channel-specific testing

A successful Simulator or text-only evaluation does not prove production channel behavior.

Before promoting a channel, test the applicable dimensions:

- authentication/token refresh;
- session creation/reconnection;
- text streaming/rendering;
- voice latency and interruption/barge-in;
- telephony routing and DTMF where used;
- rich-content rendering and sanitization;
- network/firewall/browser constraints;
- escalation/end-session metadata consumed by the channel;
- vendor-specific failure/retry behavior;
- logging/redaction behavior for the actual modality.

Keep channel tests separate from core agent-orchestration evaluations when the failure layer is outside the model/agent behavior.

## Traffic splitting

Traffic splitting became available in July 2026.

It lets one deployment channel route percentages of conversations to multiple application versions for staged rollout or A/B testing. Percentages must total 100%.

Use traffic splitting for:

- canary releases;
- controlled instruction/model/config experiments;
- gradual exposure of higher-risk changes.

Analyze versions using agreed product/business/quality metrics; BigQuery-exported interaction logs can support comparison when configured.

Do not split traffic across versions that change an external contract incompatibly unless downstream services support both.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/traffic-split

## Rollback strategy

A release plan should specify:

1. currently deployed version;
2. candidate version;
3. health/evaluation/business signals;
4. threshold for rollback;
5. known-good version;
6. external-contract compatibility;
7. channel/vendor configuration that is outside the application version and may need separate recovery.

A platform version rollback cannot undo an external side effect already committed by a backend or necessarily revert external channel/vendor configuration. Sensitive operations still require backend idempotency and compensating/business procedures.
