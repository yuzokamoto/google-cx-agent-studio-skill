# Dialogflow CX Flows and Migration

Use this reference when integrating an existing Dialogflow CX implementation or deciding whether deterministic legacy flow logic should remain in flows.

## Product distinction

CX Agent Studio agents and Dialogflow CX flows are different orchestration models.

Do not describe CX Agent Studio as a drop-in replacement for Dialogflow CX flows. Google's migration guidance explicitly treats flow-based agents as an integration/migration mechanism.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/flow

## Flow-based agents

CX Agent Studio can import a Dialogflow CX flow as a flow-based agent.

Current setup includes concepts such as:

- selecting the Dialogflow CX project/agent/flow starting resource;
- selecting an environment (draft by default in the documented workflow);
- defining the display name/description exposed to the parent CX Agent Studio agent;
- mapping CX Agent Studio variables into flow session parameters;
- mapping flow session parameters back into CX Agent Studio variables.

Verify current permissions and UI fields before implementation.

## When retaining a flow can make sense

A flow can remain useful when you already have mature, tested, deterministic logic such as:

- sequential parameter collection;
- explicit validation branches;
- authentication sequences;
- legacy integrations tightly coupled to existing Dialogflow CX flow state;
- deterministic regulated workflows that would gain little from generative reimplementation.

Do not migrate a flow merely to make the architecture appear more agentic.

## When CX Agent Studio agents are a better fit

Prefer generative agents for responsibilities such as:

- flexible natural-language interpretation;
- broad FAQ/help interactions;
- semantic routing;
- summarizing grounded information;
- multi-turn conversational tasks that do not require rigid page/state-machine control.

Keep authoritative operations behind deterministic services regardless of orchestration style.

## Migration boundary

Treat a flow-based agent as an explicit black-box capability boundary:

```text
CX Agent Studio parent agent
  -> validated input variable mapping
  -> Dialogflow CX flow
  -> explicit output/session parameter mapping
  -> CX Agent Studio variables/conversation
```

Avoid relying on undocumented shared state between the two systems.

## Migration workflow

1. Inventory the existing flow's responsibilities, parameters, integrations, and side effects.
2. Identify which behavior is genuinely deterministic and still valuable.
3. Define explicit CX→flow input mappings.
4. Define explicit flow→CX output mappings.
5. Define parent-agent routing criteria.
6. Verify permissions/environment selection.
7. Test the imported flow independently.
8. Test end-to-end handoff and state mapping in Simulator.
9. Add evaluations for entry, success, failure, and return behavior.
10. Version before replacing any production routing.

## Avoid hybrid ambiguity

Do not split ownership of one business decision across both an LLM instruction and a flow condition unless there is a clear precedence rule.

Bad pattern:

```text
Agent guesses user is authenticated
AND
Flow independently checks authentication
BUT routing depends on the guess.
```

Better:

```text
Authoritative authentication state
  -> deterministic variable/tool result
  -> Handoff Rule / explicit flow entry
  -> flow validates again where required
```

## Refactoring flows

When moving behavior from Dialogflow CX into CX Agent Studio:

- preserve the external contract first;
- move one responsibility at a time;
- create regression cases from known working conversations;
- do not simultaneously rewrite backend contracts, orchestration, and prompts unless necessary;
- compare latency, tool-call count, failure behavior, and maintainability, not only conversational quality.

## Permissions

Permission requirements can change. Follow the current flow-based-agent documentation rather than copying a role list from an older skill or migration note.
