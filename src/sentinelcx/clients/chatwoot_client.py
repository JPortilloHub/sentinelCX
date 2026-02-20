"""Chatwoot API client using httpx."""

import httpx

from sentinelcx.config import ChatwootSettings


class ChatwootClient:
    def __init__(self, settings: ChatwootSettings) -> None:
        self._base_url = settings.base_url.rstrip("/")
        self._account_id = settings.account_id
        self._client = httpx.AsyncClient(
            base_url=f"{self._base_url}/api/v1/accounts/{self._account_id}",
            headers={"api_access_token": settings.api_token},
            timeout=30.0,
        )

    async def get_conversation(self, conversation_id: int) -> dict:
        """Fetch a single conversation by ID."""
        resp = await self._client.get(f"/conversations/{conversation_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_messages(self, conversation_id: int) -> list[dict]:
        """Fetch all messages in a conversation."""
        resp = await self._client.get(f"/conversations/{conversation_id}/messages")
        resp.raise_for_status()
        data = resp.json()
        return data.get("payload", [])

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
    ) -> dict:
        """Send a message to a conversation."""
        resp = await self._client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": content, "message_type": message_type},
        )
        resp.raise_for_status()
        return resp.json()

    async def update_conversation(self, conversation_id: int, **kwargs) -> dict:
        """Update conversation attributes (priority, sla_policy_id, etc.)."""
        resp = await self._client.patch(
            f"/conversations/{conversation_id}",
            json=kwargs,
        )
        resp.raise_for_status()
        return resp.json()

    async def toggle_status(self, conversation_id: int, status: str) -> dict:
        """Toggle conversation status. Valid: open, resolved, pending, snoozed."""
        resp = await self._client.post(
            f"/conversations/{conversation_id}/toggle_status",
            json={"status": status},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_sla_status(self, conversation_id: int) -> dict:
        """Get SLA status for a conversation."""
        conversation = await self.get_conversation(conversation_id)
        sla = conversation.get("sla_policy", {})
        return {
            "conversation_id": conversation_id,
            "sla_policy": sla,
            "first_response_due": conversation.get("first_reply_created_at"),
            "status": conversation.get("status"),
        }

    async def close(self) -> None:
        await self._client.aclose()
