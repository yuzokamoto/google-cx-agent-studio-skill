# Evaluations, Simulator, Tracing, and Debugging

Use this reference for test strategy, Golden/Scenario evaluations, regression checks, Simulator traces, and systematic troubleshooting.

## Evaluation is part of implementation

Prefer this lifecycle:

```text
requirement
  -> design
  -> implementation
  -> Simulator/trace verification
  -> evaluation
  -> version
  -> deployment
```

Do not rely on a few successful manual chats as evidence of reliability.

## Evaluation types

Current CX Agent Studio documentation describes two primary test-case types.

### Golden

Use Golden evaluations for stable regression cases with known expected behavior.

Good for:

- exact/semantic conversational paths;
- required or forbidden tool calls;
- expected tool arguments/results;
- critical handoffs;
- known edge cases fixed previously.

### Scenario

Scenario evaluations use an AI-simulated end user based on a user goal and optional scenario variables/persona-style context supported by the product. They are useful for exploring conversational variation and broad coverage.

Good scenarios can help identify conversations worth promoting into stable Golden regression tests.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/evaluation

## Expectations

Current documentation supports expectations based on messages and tool calls, including conditions such as:

- Must have
- Must not have
- After tool call
- Variable value

Use expectations to encode behavioral requirements rather than relying only on an aggregate score.

Examples:

- must call `get_order_status` exactly in the supported path;
- must not call `issue_refund` before authorization state is present;
- after the lookup, the response must communicate the returned status;
- a validated variable must have the expected value.

## Tool fakes/mocks

Where supported, use tool fakes/scenario mocks to make evaluations repeatable and independent from unstable downstream systems.

Keep separate end-to-end integration tests for the real external service. A fake proves agent orchestration; it does not prove production networking/authentication/service behavior.

## Import/export

Evaluation import/export became available in June 2026 according to CX Agent Studio release notes. Use it to make evaluation assets easier to review, move between environments, and incorporate into controlled delivery workflows.

Always verify the current format/API before building automation around it.

## Minimum evaluation matrix

For every important tool-driven journey, cover:

1. happy path;
2. invalid user input;
3. no-result/business-negative path;
4. tool unavailable/error;
5. timeout/async pending where applicable;
6. duplicate user submission;
7. unexpected topic change;
8. forbidden tool call or missing prerequisite;
9. prompt injection / instruction-bypass attempt;
10. response must not expose sensitive/internal information.

For multi-agent systems, add:

- correct handoff;
- forbidden handoff;
- ambiguous routing;
- backward handoff/return path;
- state preserved correctly across agent boundaries.

## Simulator-first debugging

When something behaves incorrectly:

1. reproduce with the smallest deterministic user input;
2. open the Simulator/Preview Steps/trace;
3. identify which agent was active;
4. inspect the instruction/context available on that turn;
5. inspect model-selected tool/agent action;
6. inspect exact tool arguments;
7. inspect callback execution and modifications;
8. inspect exact tool result;
9. inspect variable/state updates;
10. inspect handoff decision;
11. compare with the expected evaluation.

Do not rewrite prompts blindly before locating the failure layer.

## Failure classification

Classify the defect before changing the system:

### Routing defect

Wrong agent or transfer decision.

Possible fixes:

- clearer descriptions/instructions;
- narrower responsibility boundaries;
- deterministic Handoff Rule;
- better prerequisite variable.

### Tool-selection defect

Correct agent, wrong/no tool.

Possible fixes:

- improve tool description;
- remove overlapping/unused tools;
- clarify tool trigger/prerequisite;
- simplify tool schema.

### Argument-prediction defect

Correct tool, wrong arguments.

Possible fixes:

- flatten schema;
- use enums/descriptions;
- inject session context deterministically;
- move normalization into callback/tool.

### Tool-runtime defect

Correct request but integration fails.

Investigate:

- endpoint/networking;
- authentication/IAM;
- timeout;
- backend response;
- MCP transport;
- OpenAPI contract.

Do not fix this with prompt text.

### State defect

Variables not set/read as expected.

Investigate:

- static vs dynamic variable type;
- callback/tool update;
- event ordering;
- new session/reset behavior;
- backend/source-of-truth mismatch.

### Response-grounding defect

Tool result is correct but answer invents/loses facts.

Possible fixes:

- reduce tool response to relevant fields;
- strengthen instruction about using only tool output;
- add after-tool filtering;
- add hallucination/semantic expectations.

### Guardrail defect

Expected block/handoff did not occur or false-positive blocks valid behavior.

Investigate the exact guardrail type/direction and test inputs before increasing broad restrictions.

## Regression workflow

When fixing a production/review issue:

1. create a minimal reproduction;
2. add/adjust a failing evaluation;
3. implement the smallest correction;
4. run related Golden and Scenario coverage;
5. verify integration path if affected;
6. create a new immutable version;
7. deploy gradually when risk warrants it.

## Trace evidence in reviews

For runtime bugs, prefer review findings that include:

```text
Expected:
Observed:
Trace evidence:
Root cause layer:
Smallest correction:
Regression test:
```

This is more maintainable than prompt-edit trial and error.

## Official references

- Evaluation: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/evaluation
- Simulator: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/simulator
- Sample applications: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/agent-sample
- Release notes: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
