# Knowledge Grounding and Retrieval

Use this reference for FAQ, documents, website knowledge, RAG, Google Search, and the boundary between retrieved knowledge and authoritative systems.

## Core rule

Choose the source based on **authority**, **freshness**, and **required determinism**, not only on convenience.

A retrieval system can ground answers in content; it should not be treated as the source of truth for transactional state unless the underlying system is explicitly designed for that purpose.

## Selection guide

| Knowledge need | Prefer |
|---|---|
| Small/simple document corpus uploaded by the application developer | File Search |
| Existing RAG knowledge base | File Search |
| Governed enterprise content backed by Vertex AI Search/Data Stores | Data Store |
| Specific websites managed/indexed through a website data store | Website/Data Store tool |
| Current public-web information | Google Search |
| Customer-specific state, balances, eligibility, order state, approvals | Backend/OpenAPI/Python/MCP tool backed by authoritative system |
| Fixed business rule that must always apply and changes rarely | Static variable/global instruction or backend policy, depending authority/sensitivity |

## File Search

File Search is documented as a simpler alternative to Data Store tools for RAG over files.

Current behavior:

- upload local files or select an existing RAG knowledge base;
- the tool searches the connected corpus;
- retrieved results are incorporated into an optimized prompt used by the calling agent;
- RAG Engine usage can incur separate costs;
- availability depends on supported RAG knowledge-base regions.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/file

Use File Search when the operational simplicity is valuable and the corpus fits its supported model.

## Data Store tools

Data Store tools provide grounded responses from configured content sources and can integrate with Vertex AI Search-backed data stores/engines.

Current documentation supports website and Cloud Storage data-store workflows from CX Agent Studio, with other data stores created through the broader AI Applications/Vertex AI Search tooling.

Use Data Store when you need stronger enterprise retrieval/governance features, larger managed corpora, website content, or existing Vertex AI Search infrastructure.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/data-store

## Website Data Store

Website data stores are appropriate when the approved knowledge source is a defined website/domain set.

Current documentation includes requirements/limitations such as domain verification and indexing constraints. Do not assume any arbitrary public URL can be used without meeting those requirements.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/website-data-store

## Google Search

Use Google Search grounding for current public information when public-web retrieval is acceptable.

Do not use Google Search for:

- private customer state;
- internal policy that must be controlled and versioned;
- regulated or contractual answers where only an approved corpus may be used;
- data that must come from a bank/CRM/order-management/system-of-record API.

## FAQ strategy

For deterministic public support knowledge such as:

- official phone numbers;
- public service hours;
- help-center procedures;
- terms and policy explanations;
- where to find a feature;
- public product descriptions;

a governed retrieval source is usually better than embedding a large FAQ directly into every agent instruction.

However, determine whether the answer must be **exactly fixed** or merely grounded:

- if wording/content must be exact and stable, use a deterministic response path or controlled backend/static configuration;
- if semantic retrieval and summarization are acceptable, use File Search/Data Store;
- if the information changes frequently and is public, consider an approved website data store or Google Search depending governance needs.

## Separate public knowledge from transactional truth

Recommended separation:

```text
Public/how-to knowledge
    -> File Search / Data Store / approved website retrieval

Current public web
    -> Google Search

Customer/account/journey state
    -> authenticated backend tool

Business decision or state mutation
    -> authoritative backend API
```

Do not allow an agent to infer a transactional fact from FAQ prose.

## Retrieval response policy

For high-trust applications, instruct the agent to:

- answer only from retrieved/authorized content for covered topics;
- avoid filling missing facts from general model knowledge when policy requires grounding;
- say that the information is unavailable when retrieval does not support the answer;
- avoid exposing internal retrieval metadata unless useful and approved;
- distinguish public informational content from personalized data.

## Corpus design

Good retrieval quality begins before the agent:

- remove stale/duplicate documents;
- use clear titles/headings;
- keep source ownership explicit;
- version policy/terms documents;
- separate conflicting regional/product policies;
- avoid indexing internal drafts as customer-facing truth;
- define a refresh/retirement process.

## Tool descriptions

Retrieval-tool descriptions should define scope precisely.

Good:

```text
Searches the approved customer help-center corpus for public support procedures, contact channels, and product usage guidance. Do not use for customer-specific account information.
```

Weak:

```text
Searches documents.
```

## Evaluation coverage

Test knowledge behavior for:

- answer present in corpus;
- answer absent from corpus;
- conflicting/stale document scenario;
- public versus personalized question;
- user asking the agent to ignore approved sources;
- retrieval tool unavailable;
- ambiguous query requiring clarification;
- unsupported claim/hallucination after retrieval.

## Do not mix products silently

Agent Assist knowledge features and CX Insights analytics are not substitutes for CX Agent Studio retrieval tools. Verify the exact product integration rather than assuming that a knowledge feature described elsewhere in Google Cloud exists in CX Agent Studio.
