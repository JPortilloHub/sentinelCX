# Sentiment Analysis Skill

## Purpose
Classify customer frustration and urgency from ticket text, returning a structured score the Triage Agent uses for routing decisions.

## Workflow

1. Read the full ticket text from the Chatwoot conversation history
2. Classify the customer's frustration level on a 0–1 scale:
   - **0.0–0.3** — Calm / informational inquiry
   - **0.3–0.6** — Mild frustration, standard priority
   - **0.6–0.8** — Significant frustration, elevated priority
   - **0.8–1.0** — Extreme frustration or anger, urgent escalation required
3. Identify supporting indicators in the text:
   - ALL CAPS usage
   - Excessive exclamation marks or question marks
   - Threat language ("cancel", "lawyer", "BBB", "report", "social media")
   - Mentions of repeated contacts ("this is my third time", "I've already called")
   - Urgency markers ("immediately", "ASAP", "right now", "unacceptable")
   - Profanity or hostile tone
4. Assess confidence in your classification (0–1):
   - High confidence (>0.8): Clear sentiment signals, unambiguous text
   - Medium confidence (0.5–0.8): Mixed signals or short text
   - Low confidence (<0.5): Ambiguous, sarcastic, or very short text

## Output Format

Return your assessment as structured JSON:

```json
{
  "score": 0.0,
  "label": "calm | mild_frustration | significant_frustration | extreme_frustration",
  "confidence": 0.0,
  "indicators": ["list of detected indicators"]
}
```

## Routing Rules

Use the sentiment score to inform the triage routing decision:
- **score < 0.3** AND confidence > 0.8 → `auto_handle` (routine inquiry)
- **score 0.3–0.8** → `needs_research` (requires investigation)
- **score > 0.8** OR confidence < 0.5 → `escalate` (needs human attention)
- VIP/enterprise customers with score > 0.5 → always `escalate`
