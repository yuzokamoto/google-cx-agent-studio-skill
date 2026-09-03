# Versioning, Export/Import, Git, and Deployment

Use this reference for immutable versions, rollback, source-control workflows, environment promotion, Web Widget/API deployment, and traffic splitting.

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
- correct version;
- environment endpoints/authentication;
- evaluations passed;
- real integration smoke tests passed;
- logging/redaction/retention settings reviewed;
- channel authentication configured;
- rollback version identified.

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

## Web Widget

Current Web Widget documentation requires authenticated requests to Google's backend using short-lived credentials. Supported patterns documented at audit time include Google-hosted/self-hosted token brokers, OAuth2, and a custom authentication API.

Do not paste an unauthenticated development embed into production and assume the snippet is sufficient.

Before production:

- choose/authenticate the intended user/service identity model;
- configure IAM least privilege;
- review origin/reCAPTCHA protections where applicable;
- sanitize any custom rich content;
- test browser/network restrictions in the real client environment;
- validate session/logout/token-refresh behavior.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/web-widget

## Rollback strategy

A release plan should specify:

1. currently deployed version;
2. candidate version;
3. health/evaluation/business signals;
4. threshold for rollback;
5. known-good version;
6. external-contract compatibility.

A platform version rollback cannot undo an external side effect already committed by a backend. Sensitive operations still require backend idempotency and compensating/business procedures.
