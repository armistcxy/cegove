# app/services/session_manager.py
import redis
import json
import uuid
from typing import Optional
from app.config import settings
from app.models.agent_state import ConversationState


class SessionManager:
    """Manages session and state for conversations."""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.ttl = 3600 * 24  # 24 hours

    def create_session(self, user_id: str) -> str:
        """Create new session."""
        session_id = str(uuid.uuid4())

        # Initialize state
        state = ConversationState(
            session_id=session_id,
            user_id=user_id,
            history=[],
            context={}
        )

        # Save to Redis
        self.redis_client.setex(
            f"session:{session_id}",
            self.ttl,
            state.model_dump_json()
        )

        return session_id

    async def get_state(self, session_id: str) -> ConversationState:
        """Get state for session."""
        data = self.redis_client.get(f"session:{session_id}")

        if not data:
            # Return default state if not found
            return ConversationState(
                session_id=session_id,
                user_id="unknown",
                history=[],
                context={}
            )

        return ConversationState.model_validate_json(data)

    async def save_state(self, session_id: str, state: ConversationState):
        """Save state for session."""
        self.redis_client.setex(
            f"session:{session_id}",
            self.ttl,
            state.model_dump_json()
        )

    async def delete_session(self, session_id: str):
        """Delete session."""
        self.redis_client.delete(f"session:{session_id}")

    def extend_session(self, session_id: str):
        """Extend session TTL."""
        self.redis_client.expire(f"session:{session_id}", self.ttl)


# Singleton instance
session_manager = SessionManager()
