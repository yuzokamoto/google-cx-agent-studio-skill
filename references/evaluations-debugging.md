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

## Golden replay modes

Golden evaluations currently support two run methods. The distinction materially changes what a passing test means.

### Stable Replay

Current API documentation defines Stable Replay as running each turn in a unique session, with previous **expected** turns injected as context. The product documentation also notes that expected variables and expected tool responses inject context in Stable Replay.

Use Stable Replay when you want to isolate whether the current turn still behaves correctly given the known-good expected prior context. It is useful for localizing regressions because a failure in an earlier generated turn does not automatically corrupt all later turns.

### Naive Replay

Current API documentation defines Naive Replay as running the golden conversation as a single session with no expected context injected. Expected variables and tool responses in the golden do not affect the result in this mode.

Use Naive Replay when you want to test whether the agent can reproduce the multi-turn path using its own actual prior outputs/state rather than receiving the golden's expected context.

### What the modes prove differently

| Question | Stable Replay | Naive Replay |
|---|---|---|
| Can this turn behave correctly with known expected prior context? | Strong fit | Not isolated |
| Can the agent carry its own generated context through the entire path? | Does not prove this end-to-end | Stronger fit |
| Are expected variables/tool responses injected as context? | Yes, per current docs | No effect on result, per current docs |
| Is one early bad generated turn likely to influence later turns in the same run? | Reduced by per-turn replay isolation | Yes, because the conversation is one session |

Do not call one mode universally better. Choose the mode based on the regression property you want to test, and use both for critical journeys when both local turn stability and end-to-end context propagation matter.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/evaluation
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1

## Expectations

Current documentation supports Golden expectations including message, tool call, and agent handoff expectations. Current API/MCP schemas also expose expectation forms for tool responses, updated variables, and no-tool-call checks where supported by the relevant evaluation representation.

Use expectations to encode behavioral requirements rather than relying only on aggregate/model-graded scores.

Examples:

- must call `get_order_status` with the required parameters;
- must not call `issue_refund` before authorization state is present;
- after the lookup, the response must communicate the returned status;
- a validated variable must have the expected value;
- no state-changing tool may be called on an informational path.

Always verify the current UI/API representation before generating importable evaluation files because supported expectation fields can differ by surface/API version.

## Evaluation metrics and their limits

Metrics answer specific questions. Do not treat any single metric as proof that the journey is correct.

### Tool correctness

Current documentation defines Tool Correctness as the percentage of expected parameters matched for an expected tool call.

Important caveats:

- a missed expected tool call scores `0`;
- a no-input expected tool call scores `1` if present;
- an unexpected tool call can cause a Golden evaluation to fail while **not changing the Tool Correctness numeric value**;
- current API schemas expose extra-tool-call matching behavior for Golden evaluation, with the documented default being failure unless configured otherwise.

Therefore, do not gate a sensitive workflow on Tool Correctness alone. Pair it with explicit forbidden/extra-call expectations or the applicable Golden extra-call policy.

### Hallucinations

Current product documentation states that the hallucination metric:

- is available for Golden and Scenario evaluations;
- is computed only for generated turns containing tool calls;
- checks claims against prior conversation, session variables, tool calls, and agent instructions;
- does **not** detect hallucinations inside the tool calls themselves because tool calls supplied as context are presumed correct;
- may return `N/A` when there is no factual claim or only already-established/common knowledge.

A clean hallucination score therefore does **not** prove that every turn in a conversation is grounded, nor that tool arguments/results are correct.

### Semantic match

For Golden evaluations, Semantic Match measures how consistent an observed utterance is with the expected utterance, currently on a `0` to `4` scale.

It is useful for regression intent/meaning but does not prove that backend state, authorization, tool execution, or hidden side effects are correct.

### User goal satisfaction

For Scenario evaluations, this binary model-graded metric measures whether the simulated user believes the goal was achieved. A scenario with no explicit or implied user goal can produce the documented sentinel score rather than a normal pass/fail signal.

User satisfaction should not replace deterministic safety expectations for authorization, forbidden tool calls, or required backend behavior.

### Scenario expectations

Current documentation describes Scenario expectations for required tool calls and agent responses.

Important caveat: unexpected tool calls are **not penalized** by Scenario tool-call expectations. Expectations specify behavior essential to satisfying the simulated user's scenario; they are not automatically a complete deny-list.

For sensitive workflows, explicitly test forbidden calls separately rather than assuming Scenario expectation success proves no extra tool executed.

### Task completion

Where exposed by the current evaluation surface, Task Completion combines user-goal satisfaction, hallucination detection, and expectations satisfaction. API fields and deprecations around aggregate metrics can evolve, so verify the current evaluation/API documentation before using this as a CI contract.

Even a positive aggregate result does not prove real downstream connectivity, authorization, persistence, or side-effect correctness.

## What evaluations do not prove

A passing CX Agent Studio evaluation does not automatically prove:

- that production networking/private connectivity works;
- that IAM/service-account/token configuration is correct in the target environment;
- that a real backend accepts or persists the request;
- that idempotency works under retries/concurrency;
- that external callbacks/webhooks arrive;
- that all unsupported/extra tool calls are absent unless the chosen test explicitly checks them;
- that non-tool turns contain no hallucinations;
- that a model-graded metric satisfies a deterministic policy requirement;
- that voice/channel-specific behavior matches production when only text was evaluated.

Use evaluations as one layer of evidence, not the whole release proof.

## Tool fakes/mocks

Where supported, use tool fakes/scenario mocks to make evaluations repeatable and independent from unstable downstream systems.

A fake-backed evaluation proves the tested agent orchestration against the mocked contract. It does **not** prove:

- DNS/network reachability;
- Service Directory/VPC path correctness;
- OAuth/IAM/secret configuration;
- actual backend schema compatibility;
- production latency/timeouts;
- persistence or side effects.

Keep separate integration/smoke tests for the real target environment.

## Recommended release-gate composition

For an important tool-driven journey, prefer multiple gates instead of one aggregate score:

1. **Deterministic expectations** for required/forbidden tools, important parameters, transfers, and variables.
2. **Golden regression metrics** with thresholds appropriate to the behavior being protected.
3. **Scenario coverage** for natural-language variation and user-goal behavior.
4. **Tool fakes** for repeatable orchestration tests where appropriate.
5. **Real integration smoke tests** for networking/authentication/backend contracts.
6. **Channel-specific tests** when production behavior depends on web/voice/platform integration.

For high-impact state changes, explicit required/forbidden behavior should take precedence over a high average model-graded score.

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

For critical Golden journeys, decide deliberately whether Stable Replay, Naive Replay, or both are required.

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

Remember that the built-in hallucination metric does not cover every turn or validate tool-call correctness by itself.

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
- Evaluation RPC schema: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1
- Simulator: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/simulator
- Sample applications: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/agent-sample
- Release notes: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/resources/release-notes
