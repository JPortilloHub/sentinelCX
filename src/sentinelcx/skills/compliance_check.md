# Compliance Check Skill

## Purpose
Scan outgoing responses for PII or policy violations before they are sent, flagging anything that needs human review.

## Workflow

Before finalizing any customer-facing response, perform ALL of the following checks:

### 1. PII Scan
Ensure the response does NOT contain:
- Social Security Numbers (SSN) or national ID numbers
- Full credit card numbers (partial/masked is OK, e.g., ending in ****1234)
- Passwords, API keys, or authentication tokens
- Internal employee IDs or internal system identifiers
- Customer's full account numbers (use masked versions)
- Other customers' personal information

### 2. Policy Scan
Verify the response does NOT contain:
- Unauthorized refund promises (amounts exceeding standard policy limits)
- SLA guarantees not specified in the customer's contract
- Legal commitments or liability admissions
- Promises of specific timelines without authorization
- Competitor comparisons that could be considered disparagement
- Pricing or discount commitments outside standard offerings

### 3. Tone Check
Ensure the response maintains:
- Professional but warm tone
- Empathy for customer frustration
- Solution-oriented language (not defensive)
- Clear, jargon-free communication
- No blame directed at the customer
- No sarcasm or condescension

### 4. Decision

If **all checks pass**: Mark as compliant and proceed with sending.

If **any check fails**: Flag for human review with specific violation details.

## Output Format

Return the compliance result as structured JSON:

```json
{
  "passed": true,
  "flags": [
    {
      "field": "pii | policy | tone",
      "issue": "Description of the specific violation",
      "severity": "critical | warning | info"
    }
  ]
}
```

## Severity Levels
- **critical**: Must be fixed before sending (PII exposure, legal liability)
- **warning**: Should be reviewed by a human (policy edge cases, tone issues)
- **info**: Minor suggestions for improvement (not blocking)
