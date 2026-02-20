"""Generates realistic markdown docs for the knowledge base."""

from pathlib import Path

PRODUCT_DOCS = {
    "products/platform-overview.md": """# SentinelCX Platform Overview

## Description
SentinelCX is an enterprise customer support intelligence platform that helps teams deliver faster, smarter support through AI-powered automation.

## Plans and Pricing

| Plan | Price | Users | Features |
|------|-------|-------|----------|
| Starter | $49/mo | Up to 5 | Basic ticketing, email support |
| Pro | $199/mo | Up to 25 | All Starter + API access, integrations, analytics |
| Enterprise | $499/mo | Unlimited | All Pro + SSO, custom dashboards, priority support, SLA guarantees |

## Key Features
- Multi-channel ticket management (email, chat, social)
- AI-powered ticket categorization and routing
- Knowledge base with semantic search
- Real-time analytics and reporting
- Third-party integrations (Salesforce, Slack, Jira, and more)
- Customizable workflows and automations
""",
    "products/integrations.md": """# Integrations Guide

## Supported Integrations

### CRM Integrations
- **Salesforce**: Full bidirectional sync. Available on Pro and Enterprise plans. Supports Accounts, Contacts, Cases, and Opportunities.
- **HubSpot**: Contact and deal sync. Available on all plans.
- **Pipedrive**: Contact sync only. Available on Pro and Enterprise plans.

### Communication Integrations
- **Slack**: Real-time notifications, escalation routing, and team collaboration. Available on all plans.
- **Microsoft Teams**: Notifications and ticket updates. Available on Pro and Enterprise plans.
- **Email**: Native email support on all plans via IMAP/SMTP or forwarding.

### Developer Integrations
- **REST API**: Full API access on Pro and Enterprise plans. Rate limits: 100 req/min (Pro), 1000 req/min (Enterprise).
- **Webhooks**: Available on Pro and Enterprise. Supports conversation_created, message_created, conversation_resolved, and 15+ other events.
- **Zapier**: 50+ pre-built Zaps. Available on all plans.

### SSO/Authentication
- **Okta**: SAML 2.0 SSO. Enterprise plan only.
- **Azure AD**: SAML 2.0 and OIDC. Enterprise plan only.
- **Google Workspace**: OAuth 2.0. Available on Pro and Enterprise plans.

## Setup Instructions
Each integration has a dedicated setup guide accessible from Settings → Integrations in your dashboard.
""",
    "products/api-reference.md": """# API Reference

## Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_TOKEN
```

## Rate Limits
- Pro plan: 100 requests/minute
- Enterprise plan: 1000 requests/minute
- Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## Endpoints

### Conversations
- `GET /api/v1/conversations` — List conversations
- `GET /api/v1/conversations/:id` — Get conversation details
- `POST /api/v1/conversations` — Create conversation
- `PATCH /api/v1/conversations/:id` — Update conversation

### Messages
- `GET /api/v1/conversations/:id/messages` — List messages
- `POST /api/v1/conversations/:id/messages` — Send message

### Contacts
- `GET /api/v1/contacts` — List contacts
- `GET /api/v1/contacts/:id` — Get contact details
- `POST /api/v1/contacts` — Create contact

### Data Export
- `POST /api/v1/exports` — Request data export (CSV or JSON format)
- `GET /api/v1/exports/:id` — Check export status and download

## Webhook Events
Configure webhooks at Settings → Webhooks. Available events:
- `conversation_created` — New conversation started
- `conversation_resolved` — Conversation marked as resolved
- `message_created` — New message in a conversation
- `contact_created` — New contact added
- `assignee_changed` — Conversation reassigned

## Error Codes
- 400: Bad Request — Invalid parameters
- 401: Unauthorized — Invalid or missing API token
- 403: Forbidden — Insufficient permissions
- 404: Not Found — Resource doesn't exist
- 429: Too Many Requests — Rate limit exceeded
- 500: Internal Server Error — Contact support if persistent
""",
    "products/mobile-app.md": """# Mobile App Guide

## Supported Platforms
- **iOS**: Version 18.0 and above. Available on App Store.
- **Android**: Version 13 and above. Available on Google Play.

## Features
- View and respond to conversations
- Push notifications for new messages and assignments
- Quick reply templates
- Offline mode for viewing cached conversations

## Push Notifications
Push notifications require:
1. Notification permissions enabled in device settings
2. Notification preferences enabled in-app (Settings → Notifications)
3. A valid push token registered with our servers

### Troubleshooting Notifications
If notifications aren't working:
1. Check device notification settings
2. Check in-app notification preferences
3. Try logging out and back in to refresh the push token
4. Ensure you're on the latest app version
5. For iOS: Check that Background App Refresh is enabled

## Known Issues (Current Version)
- iOS 18.2: Push notification token refresh issue after system update. Fix in progress, expected in next release.
- Android: Battery optimization may delay notifications. Add app to battery optimization exceptions.

## Data Import Tool
The mobile app supports importing data via:
- **CSV files**: Comma-separated values with headers
- **JSON files**: Array of objects matching our schema
- **Excel files (.xlsx)**: First sheet only, with headers in row 1
""",
}

POLICY_DOCS = {
    "policies/refund-policy.md": """# Refund Policy

## Standard Refund Terms
- Full refund available within 14 days of initial purchase
- Prorated refund available for annual plans cancelled mid-term
- Monthly plans: No refund for partial months, but service continues until end of billing period
- Enterprise plans: Refunds handled per individual contract terms

## Refund Processing
- Refunds are processed within 5-10 business days
- Refunds are issued to the original payment method
- A confirmation email is sent when the refund is initiated

## Exceptions
- Promotional or discounted subscriptions: Refund amount is based on the price actually paid
- Add-on services: Refundable within 7 days of purchase
- Custom enterprise features: Non-refundable once development has begun

## Dispute Resolution
If a customer disputes a charge:
1. Attempt to resolve directly with the customer first
2. If unresolved, escalate to the billing team
3. Provide transaction details and communication history
4. Billing team will review and respond within 2 business days

## Agent Guidelines
- Agents can approve refunds up to $100 without manager approval
- Refunds $100-$500 require team lead approval
- Refunds over $500 require manager approval
- Always document the reason for the refund in the ticket notes
""",
    "policies/sla-terms.md": """# Service Level Agreement (SLA) Terms

## Response Time SLAs

| Priority | Starter | Pro | Enterprise |
|----------|---------|-----|------------|
| Urgent | 24h | 4h | 1h |
| High | 48h | 8h | 2h |
| Medium | 72h | 24h | 8h |
| Low | 5 business days | 48h | 24h |

## Uptime Guarantee
- Starter: No uptime SLA
- Pro: 99.5% monthly uptime
- Enterprise: 99.9% monthly uptime with service credits

## Service Credits (Enterprise Only)
- Below 99.9% but above 99.0%: 10% credit
- Below 99.0% but above 95.0%: 25% credit
- Below 95.0%: 50% credit

## Escalation Procedures
1. **Level 1**: Front-line support agent (initial response)
2. **Level 2**: Senior support engineer (complex technical issues)
3. **Level 3**: Engineering team (bugs, infrastructure issues)
4. **Level 4**: Management (SLA breaches, VIP escalations)

## Maintenance Windows
- Scheduled maintenance: Sundays 2:00-6:00 AM UTC (announced 48h in advance)
- Emergency maintenance: As needed with best-effort notification
- Maintenance time is excluded from uptime calculations
""",
    "policies/data-retention.md": """# Data Retention Policy

## Standard Retention Periods
- Active account data: Retained for the duration of the subscription
- Conversation history: 2 years from conversation close date
- Audit logs: 1 year
- Analytics data: 1 year (aggregated data retained indefinitely)

## After Account Cancellation
- Data is retained for 30 days after cancellation
- Customer can request data export during this period
- After 30 days, data is permanently deleted
- Backup copies are purged within 90 days

## Data Export
- Available formats: CSV, JSON
- Export includes: conversations, contacts, notes, attachments
- Large exports may take up to 24 hours to generate
- Download link valid for 7 days

## Compliance
- GDPR: Full compliance including right to erasure
- SOC 2 Type II: Certified (report available on request for Enterprise customers)
- HIPAA: BAA available for Enterprise plan customers in healthcare
- Data residency: US (default), EU, and APAC options available for Enterprise

## Right to Erasure (GDPR)
- Customers can request deletion of all their data
- Request processed within 30 days
- Confirmation provided upon completion
""",
}

FAQ_DOCS = {
    "faqs/common-issues.md": """# Common Issues & Troubleshooting

## Login Issues

### "Invalid credentials" error
1. Verify your email address is correct
2. Try resetting your password via the "Forgot Password" link
3. Check if your account has been deactivated (contact admin)
4. Clear browser cache and cookies
5. If using SSO, check with your IT admin that your SSO account is active

### Account locked
- Accounts are locked after 5 failed login attempts
- Lock expires automatically after 30 minutes
- Contact support for immediate unlock

## Performance Issues

### Slow page loads
1. Check your internet connection speed
2. Clear browser cache
3. Try a different browser (Chrome/Firefox recommended)
4. Disable browser extensions that may interfere
5. If issues persist across multiple users, contact support with specifics

### API timeout errors
- Ensure you're not exceeding rate limits
- Check API status page for any known issues
- For large data requests, use pagination
- Consider implementing exponential backoff for retries

## Email Issues

### Not receiving notification emails
1. Check spam/junk folder
2. Verify notification preferences in Settings → Notifications
3. Check that your email provider isn't blocking our domain
4. Whitelist notifications@sentinelcx.com

### Email formatting issues
- Ensure your email client supports HTML emails
- If using Outlook, check rendering in the web version
""",
    "faqs/billing-faq.md": """# Billing FAQ

## When am I charged?
- Monthly plans: Charged on the same date each month as your signup date
- Annual plans: Charged once per year on your signup anniversary
- Mid-month signups: First month is prorated

## How do I change my plan?
1. Go to Settings → Billing → Change Plan
2. Select your new plan
3. Upgrades take effect immediately; downgrades at next billing cycle
4. Prorated charges/credits are applied automatically

## How do I update my payment method?
1. Go to Settings → Billing → Payment Methods
2. Add a new payment method
3. Set it as default
4. Remove the old method if desired

## What happens if my payment fails?
1. First attempt: Automatic retry after 24 hours
2. Second attempt: Retry after 3 days, warning email sent
3. Third attempt: Retry after 7 days, account flagged
4. After 14 days: Account suspended (read-only access)
5. After 30 days: Account data deletion scheduled

## Can I get a receipt?
Yes! Receipts are automatically emailed after each payment. You can also download past receipts from Settings → Billing → Payment History.

## Do you offer discounts?
- Annual billing: 20% discount vs monthly
- Nonprofits: 30% discount (verification required)
- Education: 50% discount (verification required)
- Startups: Contact sales for special pricing
""",
    "faqs/account-management.md": """# Account Management FAQ

## How do I add team members?
1. Go to Settings → Team → Invite Members
2. Enter email addresses (comma-separated for bulk)
3. Select their role (Agent, Admin, or Observer)
4. They'll receive an invitation email

## Roles and Permissions

| Permission | Agent | Admin | Owner |
|-----------|-------|-------|-------|
| View conversations | Yes | Yes | Yes |
| Respond to conversations | Yes | Yes | Yes |
| Manage team members | No | Yes | Yes |
| Access billing | No | No | Yes |
| Configure integrations | No | Yes | Yes |
| View analytics | Yes | Yes | Yes |
| Export data | No | Yes | Yes |

## How do I cancel my account?
1. Go to Settings → Account → Cancel Account
2. Select your reason for cancellation
3. Confirm cancellation
4. Your data will be retained for 30 days (see Data Retention Policy)

## How do I transfer account ownership?
1. Current owner goes to Settings → Account → Transfer Ownership
2. Select the new owner (must be an existing Admin)
3. New owner confirms via email
4. Transfer is immediate and irreversible

## How do I enable two-factor authentication (2FA)?
1. Go to Settings → Security → Two-Factor Authentication
2. Scan the QR code with your authenticator app
3. Enter the verification code to confirm
4. Save your backup codes in a secure location
""",
}


def generate_knowledge_base(output_dir: str = "knowledge_base") -> dict:
    """Generate all knowledge base markdown files."""
    output_path = Path(output_dir)
    stats = {"files_created": 0, "categories": []}

    all_docs = {**PRODUCT_DOCS, **POLICY_DOCS, **FAQ_DOCS}

    for relative_path, content in all_docs.items():
        file_path = output_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.strip() + "\n", encoding="utf-8")
        stats["files_created"] += 1

    # Collect category stats
    for subdir in sorted(output_path.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            docs = list(subdir.rglob("*.md"))
            stats["categories"].append({"name": subdir.name, "documents": len(docs)})

    return stats
