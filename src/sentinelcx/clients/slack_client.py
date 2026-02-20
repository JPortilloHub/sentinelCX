"""Slack API client wrapper using slack-sdk."""

from slack_sdk.web.async_client import AsyncWebClient

from sentinelcx.config import SlackSettings


class SlackClient:
    def __init__(self, settings: SlackSettings) -> None:
        self._client = AsyncWebClient(token=settings.bot_token)
        self._escalation_channel = settings.escalation_channel

    async def post_message(self, channel: str, text: str, blocks: list | None = None) -> dict:
        """Post a message to a Slack channel."""
        kwargs: dict = {"channel": channel, "text": text}
        if blocks:
            kwargs["blocks"] = blocks
        resp = await self._client.chat_postMessage(**kwargs)
        return resp.data

    async def post_escalation(self, text: str, blocks: list | None = None) -> dict:
        """Post an escalation message to the configured escalation channel."""
        return await self.post_message(self._escalation_channel, text, blocks)

    async def get_channel_members(self, channel: str) -> list[str]:
        """Get list of member user IDs in a channel."""
        resp = await self._client.conversations_members(channel=channel)
        return resp.data.get("members", [])

    async def get_user_info(self, user_id: str) -> dict:
        """Get user profile information."""
        resp = await self._client.users_info(user=user_id)
        return resp.data.get("user", {})

    async def get_team_availability(self, channel: str) -> list[dict]:
        """Check availability of team members in a channel."""
        members = await self.get_channel_members(channel)
        availability = []
        for member_id in members:
            presence = await self._client.users_getPresence(user=member_id)
            user_info = await self.get_user_info(member_id)
            availability.append(
                {
                    "user_id": member_id,
                    "name": user_info.get("real_name", ""),
                    "presence": presence.data.get("presence", "away"),
                    "available": presence.data.get("presence") == "active",
                }
            )
        return availability
