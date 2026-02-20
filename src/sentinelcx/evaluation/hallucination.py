"""Hallucination detection using a secondary Claude call."""

import logging

import anthropic

from sentinelcx.config import Settings

logger = logging.getLogger(__name__)

HALLUCINATION_CHECK_PROMPT = """You are a fact-checking assistant. Your job is to identify any claims in the "Response" that are NOT supported by the "Source Documents" provided.

## Source Documents
{sources}

## Response to Check
{response}

## Instructions
1. Examine each factual claim in the Response
2. Check if it is supported by the Source Documents
3. Flag any claims that are not supported or are contradicted by the sources
4. Be strict: if a claim cannot be verified from the sources, flag it

Return your analysis as JSON:
{{
  "hallucination_detected": true/false,
  "flagged_claims": [
    {{
      "claim": "The specific claim text",
      "issue": "not_supported | contradicted | fabricated",
      "explanation": "Why this claim is problematic"
    }}
  ],
  "confidence": 0.0-1.0,
  "summary": "Brief overall assessment"
}}"""


async def check_response_for_hallucination(
    response_text: str,
    source_documents: list[str],
    settings: Settings,
) -> dict:
    """Check a single response for hallucinations against its source documents."""
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    sources_text = "\n\n---\n\n".join(
        f"Document {i + 1}:\n{doc}" for i, doc in enumerate(source_documents)
    )

    prompt = HALLUCINATION_CHECK_PROMPT.format(
        sources=sources_text,
        response=response_text,
    )

    try:
        message = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        result_text = message.content[0].text

        # Try to parse JSON from the response
        import json
        import re

        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"raw_response": result_text, "hallucination_detected": None}
    except Exception as e:
        logger.error("Hallucination check failed: %s", e)
        return {"error": str(e), "hallucination_detected": None}


async def detect_hallucinations(
    settings: Settings,
    responses: list[dict] | None = None,
) -> dict:
    """Run hallucination detection on a batch of responses.

    Each response dict should have: {"response_text": str, "source_documents": [str]}
    """
    if not responses:
        return {"error": "No responses provided for hallucination check"}

    results = []
    flagged_count = 0

    for resp in responses:
        check = await check_response_for_hallucination(
            response_text=resp["response_text"],
            source_documents=resp.get("source_documents", []),
            settings=settings,
        )
        results.append(check)
        if check.get("hallucination_detected"):
            flagged_count += 1

    return {
        "total_checked": len(results),
        "flagged": flagged_count,
        "hallucination_rate": round(flagged_count / len(results), 3) if results else 0.0,
        "details": results,
    }
