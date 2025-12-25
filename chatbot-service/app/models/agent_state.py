# app/models/agent_state.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ConversationState(BaseModel):
    """
    Simplified conversation state for Claude-based agent.
    No complex booking flow tracking - Claude handles the flow naturally.
    """
    session_id: str
    user_id: str
    history: List[Dict[str, Any]] = []  # Claude message format
    context: Dict[str, Any] = {}  # Store focused movie, last query, etc.

    def add_message(self, role: str, content: str):
        """Add message to history in Claude format."""
        self.history.append({"role": role, "content": content})

    def get_recent_history(self, max_messages: int = 10) -> List[Dict]:
        """Get recent messages for context window."""
        return self.history[-max_messages:]

    def set_context(self, key: str, value: Any):
        """Set context value (focused movie, pending action, etc.)."""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value."""
        return self.context.get(key, default)

    def clear_context(self):
        """Clear all context."""
        self.context = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "history": self.history,
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Create from dict."""
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            history=data.get("history", []),
            context=data.get("context", {})
        )
