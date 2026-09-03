# Security, Guardrails, Privacy, and Authentication

Use this reference for prompt injection, output restrictions, PII handling, redaction, authentication, tool authorization, Web Widget security, and high-trust application design.

## Defense in depth

Do not treat guardrails as the only security layer.

Use multiple boundaries:

```text
User/channel controls
  -> CX Agent Studio guardrails/instructions
  -> callbacks/tool validation
  -> authenticated API boundary
  -> authorization/business rules
  -> downstream system controls
```

The LLM must never be the sole authorization mechanism.

## Guardrail families

Current CX Agent Studio documentation includes:

### Prompt Guard

Provides protection against prompt-based attacks. Current outcomes include:

- Say exactly
- Handoff to an agent
- Generate a response

Do not describe a generic `Custom` Prompt Guard outcome unless the current UI/docs explicitly add one.

### Blocklist

Use for deterministic word/phrase/regex restrictions on user input and/or agent response where the feature supports it.

Do not block data on user input if the legitimate journey must receive that data. For example, an output-only PII pattern can be safer than blocking the same pattern on both directions.

### Safety

Current high-level safety levels include Relaxed, Balanced, and Strict, with category customization available. Choose based on the application and test false positives; do not claim one level is universally correct.

### Rules

Custom guardrail rules can use natural-language behavior or code-backed behavior according to current product support. Use them for application-specific output/input restrictions that do not belong in a backend authorization rule.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/guardrail

## Prompt injection

Design as though users may ask the agent to:

- ignore previous instructions;
- reveal system prompts/tool schemas;
- fabricate tool results;
- skip authentication/consent;
- impersonate an internal system;
- call a tool with unapproved parameters;
- reveal hidden/internal decision criteria.

Controls:

- enable/test Prompt Guard where appropriate;
- keep secrets out of prompts/model context;
- enforce authorization in backend/tool code;
- give agents minimum tool access;
- filter tool results before model exposure;
- use deterministic handoff/prerequisite checks for sensitive capabilities;
- add adversarial evaluation cases.

## PII and sensitive data

Separate these questions:

1. May the user provide this data through this channel?
2. Does the model need to see the full value?
3. Does the value need to be stored as a CX variable?
4. May it appear in logs/history/evaluations?
5. May it be repeated to the user?
6. What system is authorized to persist/process it?

Minimize every answer.

### Redaction

CX Agent Studio application settings currently provide automatic redaction and logging controls. Enabling redaction does not remove the need to test the exact sensitive formats used by your application.

A custom identifier format may not be covered as expected. Test logs/traces with approved synthetic data before production.

Settings reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/settings

## Secrets

Never place API keys, credentials, private tokens, or sensitive authorization material in:

- agent instructions;
- static/dynamic variables visible to the model unless explicitly designed for that purpose;
- user-visible tool errors;
- evaluation prompts;
- repository examples.

Use supported authentication/Secret Manager/IAM mechanisms and least privilege.

## Tool authorization

A successful tool-selection prediction is not authorization.

The backend/tool must validate:

- caller identity where required;
- end-user identity/session proof where required;
- permission to perform the requested action;
- request integrity/business prerequisites;
- idempotency for sensitive mutations.

Do not trust a user-supplied identifier simply because it matches a format.

## OpenAPI/MCP authentication

Authentication options evolve; verify the current tool documentation before implementation.

For MCP, current documentation states that MCP tools use the same authentication options as OpenAPI tools and supports custom headers derived from session variables. Only Streamable HTTP transport is currently documented as supported.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/open-api
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/mcp

## Web Widget authentication

Current documentation states that API requests made by the Web Widget to Google's backend must be authenticated with a short-lived OAuth 2.0 access token.

Documented patterns include:

- Google-hosted token broker;
- self-hosted token broker;
- OAuth2;
- custom authentication API returning an appropriate Google access token or signed JWT.

The Google-hosted public-access option supports origin and reCAPTCHA checks; verify current details before deployment.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/web-widget

## Browser security

Treat widget integration as application code, not a trusted isolated iframe by default. Follow current widget security guidance, sanitize custom content, and consider the effect of same-origin browser storage access where applicable.

Do not infer that a URL allowlist or origin setting provides complete application authorization.

## Logging and retention

Before enabling Interaction Data, Cloud Logging, BigQuery export, or audio recording, establish:

- purpose;
- retention;
- access controls;
- redaction expectations;
- environment separation;
- whether production PII is allowed;
- evaluation/test-data policy.

Do not use real customer credentials/biometrics/secrets in test fixtures.

## High-stakes decisions

For financial, healthcare, identity, compliance, or other high-impact workflows:

- the model may explain and collect conversational context;
- deterministic services should validate identity, eligibility, authorization, and state transitions;
- do not expose internal scoring/fraud/risk criteria unless intentionally approved;
- use neutral failure messaging where detailed error distinctions would leak sensitive state;
- explicitly test prompt-injection and bypass attempts.

## Security review checklist

- [ ] Prompt Guard behavior tested
- [ ] Safety level chosen from application requirements, not default habit
- [ ] Blocklists scoped to the correct direction
- [ ] Secrets absent from prompts/repository
- [ ] PII collection minimized
- [ ] Redaction empirically tested
- [ ] Tool access least-privilege
- [ ] Backend authorizes every sensitive operation
- [ ] Session identifiers are not treated as user authentication by themselves
- [ ] Error responses are customer-safe
- [ ] Logging/retention approved
- [ ] Web Widget authentication configured
- [ ] Adversarial evaluations cover bypass attempts
