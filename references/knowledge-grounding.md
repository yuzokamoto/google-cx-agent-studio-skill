# Knowledge Grounding and Retrieval

Use this reference for FAQ, documents, website knowledge, RAG, Google Search, and the boundary between retrieved knowledge and authoritative systems.

## Core rule

Choose the source based on **authority**, **freshness**, **content/source type**, **retrieval controls**, and **required determinism**, not only on convenience.

A retrieval system can ground answers in content; it should not be treated as the source of truth for transactional state unless the underlying system is explicitly designed for that purpose.

When describing product capabilities, follow `source-policy.md`: distinguish what Google documents from architecture recommendations built on those capabilities.

## Capability-based selection guide

| Requirement | Capability to evaluate |
|---|---|
| Upload local files directly for RAG with minimal setup | File Search |
| Reuse an existing RAG knowledge base | File Search |
| Use Vertex AI Search Data Stores or Engines | Data Store |
| Search approved website content | Website Data Store / Data Store |
| Search unstructured Cloud Storage documents | Cloud Storage Data Store |
| Use structured question/answer data with FAQ semantics | FAQ Data Store |
| Search connector-backed enterprise content | Data Store with supported `CONNECTOR` source |
| Need Data Store filtering/engine search/boosting or text-vs-voice retrieval configuration | Data Store, when the current feature set matches the requirement |
| Current unrestricted public-web grounding | Google Search, when policy allows public-web retrieval |
| Customer-specific state, balances, eligibility, order state, approvals | Tool backed by the authoritative system |
| Stable conversational/presentation policy that does not enforce an authoritative invariant | Static variable/global instruction |
| Business rule, authorization, compliance requirement, or state invariant that must hold regardless of model behavior | Authoritative backend/service that owns and enforces the rule |

This table is a decision aid, not a claim that one retrieval product is universally “more enterprise” or “more governed” than another.

## File Search

**Documented:** Google describes File Search as a **simpler alternative to Data Store tools** for Retrieval Augmented Generation over files.

Current documented behavior includes:

- upload local files or select an existing RAG knowledge base;
- when local files are uploaded, a RAG knowledge base is created;
- search the connected RAG knowledge base;
- produce an optimized prompt containing the user query, retrieved results, and answer-writing instructions for the calling agent;
- RAG Engine incurs its own usage cost;
- RAG knowledge-base region support is constrained to the currently documented locations.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/file

**Recommended:** prefer File Search when the primary need is straightforward file-backed RAG and its supported corpus/region model is sufficient. Do not infer broader governance, filtering, connector, or website-ingestion capabilities that the File Search documentation does not establish.

## Data Store tools

**Documented:** Data Store tools ground agent responses in configured Data Stores/Engines backed by Vertex AI Search capabilities.

Current documented capabilities include:

- use existing Data Stores;
- create Website or Cloud Storage Data Stores from the CX Agent Studio workflow;
- use other Data Stores created through AI Applications where supported;
- attach one or more compatible Data Stores;
- asynchronous execution;
- filter behavior controls;
- text/voice modality-specific rewriter/summarization/grounding configuration;
- search a specific Data Store or an Engine, depending on the API configuration;
- filter and boosting capabilities exposed by current schemas.

Current v1 schemas identify these Data Store types:

- `PUBLIC_WEB` — public web content;
- `UNSTRUCTURED` — unstructured private data;
- `FAQ` — structured FAQ data;
- `CONNECTOR` — connector-backed first- or third-party content.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/data-store
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/projects.locations.apps.tools

**Recommended:** choose Data Store because a concrete capability is required—for example website ingestion, structured FAQ semantics, an existing Vertex AI Search estate, connector-backed content, filtering/boosting, or Data Store/Engine-level search—not because of a vague “stronger governance” label.

## Cloud Storage Data Store

**Documented:** the Cloud Storage Data Store workflow supports unstructured documents and FAQ content sourced from Cloud Storage.

For unstructured content, use it for documents such as PDFs, HTML, or text according to current supported formats/workflows.

For source refresh, the current creation workflow exposes one-time or periodic synchronization, with current configuration constraints that should be checked before implementation.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/cloud-storage-data-store

## FAQ Data Store

**Documented:** `FAQ` is a current Data Store type for structured question-and-answer data.

The current Cloud Storage FAQ workflow documents:

- CSV-based structured FAQ ingestion;
- question/answer pairs with optional title/URL fields;
- when a user question matches an uploaded FAQ question with high confidence, the agent returns the corresponding answer **without modification**.

This behavior is especially relevant when approved customer-facing wording should be preserved for matched FAQ answers.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/cloud-storage-data-store

**Recommended:** evaluate FAQ Data Store before inventing a custom exact-answer mechanism when the requirement is naturally a maintained structured FAQ corpus. Still test matching behavior, absent answers, stale content, and whether exact returned wording satisfies the application's legal/content policy.

Do not confuse an exact FAQ answer with enforcement of an authoritative business rule. FAQ is informational retrieval, not authorization or transactional state control.

## Website Data Store

**Documented:** Website Data Store is designed to search/retrieve content from specified websites through a Data Store.

Current documented constraints include:

- domain verification;
- public content must be available to Google's search/indexing process as documented;
- current page-count/indexing limits;
- include/exclude URL patterns.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/website-data-store

**Recommended:** use this path when the approved source of truth is a controlled website/domain corpus and the current indexing requirements are acceptable. Do not assume any arbitrary URL can be used immediately.

## Google Search

Use Google Search grounding for current public information when unrestricted/current public-web retrieval is acceptable under the application's policy.

Do not use Google Search as a substitute for:

- private customer state;
- internal policy that must come only from an approved controlled corpus;
- contractual/regulatory answers restricted to approved sources;
- data that must come from a CRM/order/banking/system-of-record API.

## Authority is separate from retrieval technology

“Governed” is primarily an application/data-management property, not a blanket ranking of retrieval tools.

For any retrieval source, ask:

1. Who owns and approves the content?
2. How is stale content retired?
3. Are drafts excluded from customer-facing retrieval?
4. How is access to the underlying corpus controlled?
5. What region/residency constraints apply?
6. How is content refreshed/synchronized?
7. Are citations/source attribution required?
8. What happens when sources conflict?
9. Must exact wording be returned, or is summarization allowed?
10. Which topics must fall back instead of using general model knowledge?

A tool does not create content governance automatically; governance comes from the full source, access, lifecycle, retrieval, and application-policy design.

## Separate public knowledge from transactional truth

Recommended separation:

```text
Approved informational corpus
    -> File Search / Data Store / Website or FAQ retrieval

Current public web
    -> Google Search when approved

Customer/account/journey state
    -> authenticated authoritative backend tool

Business decision or state mutation
    -> authoritative backend API/service
```

Do not allow an agent to infer a transactional fact from FAQ/document prose.

## Retrieval response policy

For high-trust applications, consider instructing the agent to:

- answer only from retrieved/authorized content for covered topics;
- avoid filling missing facts from general model knowledge when policy requires grounding;
- say the information is unavailable when the authorized corpus does not support the answer;
- avoid exposing internal retrieval metadata unless useful and approved;
- distinguish public informational content from personalized data.

These are **recommended application policies**, not automatic guarantees of File Search or Data Store.

## Corpus design

Good retrieval quality begins before the agent:

- remove stale/duplicate documents;
- use clear titles/headings;
- keep source ownership explicit;
- version policy/terms documents;
- separate conflicting regional/product policies;
- avoid indexing internal drafts as customer-facing truth;
- define refresh/retirement behavior;
- maintain structured FAQ content as structured FAQ where that representation is useful.

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
- exact FAQ match where applicable;
- paraphrased FAQ question;
- conflicting/stale document scenario;
- public versus personalized question;
- user asking the agent to ignore approved sources;
- retrieval tool unavailable;
- ambiguous query requiring clarification;
- filter/source selection where used;
- unsupported claim/hallucination after retrieval;
- exact wording preservation when required.

## Do not mix products silently

Agent Assist knowledge features and CX Insights analytics are not substitutes for CX Agent Studio retrieval tools. Verify the exact product integration rather than assuming that a knowledge feature described elsewhere in Google Cloud exists in CX Agent Studio.
