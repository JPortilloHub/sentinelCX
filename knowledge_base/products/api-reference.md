# API Reference

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
