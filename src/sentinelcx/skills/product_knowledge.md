# Product Knowledge Skill

## Purpose
A retrieval-augmented skill that pulls the latest product specs and compatibility info from the knowledge base before drafting a response.

## Workflow

1. **Search before answering**: Before making any factual claim about products, features, pricing, or compatibility, you MUST use the `search_knowledge_base` tool to find relevant documentation.
2. **Verify facts**: For each factual claim in your response, verify it against at least one knowledge base document. Cross-reference multiple documents when possible for accuracy.
3. **Cite sources**: Include the source document path for every fact you reference. Format citations as `[source: <file_path>]`.
4. **Handle gaps honestly**: If the knowledge base has no relevant information for a question:
   - State explicitly: "I don't have documentation on this specific topic."
   - NEVER fabricate product specifications, pricing, compatibility information, or feature details.
   - Suggest the customer contact a specialist or check the official documentation.
5. **Use get_document for detail**: When a search result looks relevant but you need more context, use the `get_document` tool to read the full document.
6. **Check list_topics first**: For broad or exploratory questions, start with `list_topics` to understand what documentation categories are available.

## Product Categories

Common knowledge base categories to search:
- `products/` — Feature specs, compatibility matrices, setup guides, release notes
- `policies/` — Refund policy, SLA terms, data retention, escalation procedures
- `faqs/` — Common troubleshooting, billing questions, account management

## Quality Checks

Before including any product information in your response:
- Is the information from a knowledge base document? (not from your training data)
- Is the source document current? (check for version or date references)
- Does the information directly answer the customer's specific question?
- Are there any caveats or conditions mentioned in the source that should be included?
