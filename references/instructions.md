# Instructions and Prompt Design

Use this reference for agent instructions, global instructions, XML restructuring, examples, references, and prompt-maintenance decisions.

## Language

Google's current documentation recommends writing agent prompts/instructions in **English** for the highest instruction-following quality. Configure or instruct the end-user response language separately.

Official reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/instruction

## Supported references

Use recognized references rather than plain-text names when linking application objects:

```text
Dynamic variable: {variable_name}
Static variable:  {{variable_name}}
Tool:             {@TOOL: tool_name}
Agent:            {@AGENT: Agent Name}
```

Use the builder's reference picker/chips when working in the console so references resolve to actual application resources.

## Static versus dynamic variables in instructions

Do not use the old assumption that every variable behaves the same way.

- **Static variables** use `{{variable_name}}`. They are compiled into the prompt as direct substitution and are suitable for stable configuration/rules. Changing them invalidates prompt caching and may increase latency.
- **Dynamic variables** use `{variable_name}`. Updates are represented as state-update events in conversation history rather than direct text substitution.

See `state-callbacks-determinism.md`.

## Instruction structure

Natural language is supported. Google also provides **Restructure instructions**, which can organize instructions into an XML-style structure that may improve model adherence.

A practical shape is:

```xml
<role>
Define the agent's responsibility and boundary.
</role>

<persona>
Define tone and user-facing behavior only where it matters.
</persona>

<taskflow>
  <subtask name="...">
    <step>
      <trigger>Observable condition.</trigger>
      <action>Specific behavior, tool call, or handoff.</action>
    </step>
  </subtask>
</taskflow>

<constraints>
Rules the agent must not violate.
</constraints>
```

The tags are a structure aid, not a replacement for clear logic.

## Global instruction versus agent instruction

Put a rule in **global instruction** when it truly applies to every agent, such as:

- brand-wide response language/tone;
- universal privacy/security constraints;
- shared disclosure requirements;
- application-wide prohibitions.

Keep it in an **agent instruction** when it is local to one responsibility, tool, or journey.

Avoid duplicating the same rule in global and local instructions unless the duplication is deliberate and tested. Duplicated wording can drift and create conflicting sources of truth.

## Write observable triggers

Prefer conditions the application can actually observe.

Good:

```xml
<trigger>The user asks for the status of an existing order.</trigger>
```

Risky:

```xml
<trigger>The user is probably a high-value customer.</trigger>
```

If the condition must be guaranteed, derive it from a validated variable/tool result and use deterministic controls rather than prose alone.

## Tool instructions

A tool instruction should establish:

- **when** the tool is appropriate;
- required prerequisites;
- whether it can be called more than once;
- how to handle success, no-result, pending, and failure states;
- what must not be inferred from the result.

Do not paste an API specification into the instruction. The tool schema/description is the contract; the instruction should cover orchestration policy.

## Agent references

When routing via instruction, describe semantic ownership clearly:

```xml
<step>
  <trigger>The user wants to return a purchased item.</trigger>
  <action>Transfer to {@AGENT: Returns Agent}.</action>
</step>
```

If the transfer condition must be deterministic, use a Handoff Rule instead of relying exclusively on this instruction.

## Few-shot examples

Use examples only when clear declarative instructions are insufficient.

Good reasons:

- recurring formatting errors;
- nuanced tool-selection behavior;
- a conversational edge case that remains unstable after instruction cleanup.

Avoid large example catalogs. They increase context, maintenance cost, and the chance of accidental overfitting.

## Keep instructions maintainable

Prefer:

- one authoritative rule per concept;
- short sections grouped by responsibility;
- explicit negative constraints only for meaningful failure modes;
- references to real tools/agents instead of duplicated descriptions;
- state names/enums that match backend/tool contracts where possible.

Avoid:

- giant monolithic prompts containing API docs;
- hidden business logic expressed only as prose;
- duplicated policies across many agents;
- instructions describing features that do not exist yet;
- relying on the model to maintain counters, authorization state, or irreversible workflow state.

## Review checklist

When auditing instructions, check:

1. Is the role specific and non-overlapping with sibling agents?
2. Are tool/agent/variable references valid?
3. Are static/dynamic variable syntaxes correct?
4. Are deterministic requirements wrongly expressed as prose?
5. Are tool failure/pending/no-result paths covered?
6. Are there contradictory global and local rules?
7. Is user-facing language behavior explicit where needed?
8. Are examples necessary and minimal?
9. Could a smaller tool response eliminate prompt complexity?
10. Are there evaluation cases for the important constraints?
