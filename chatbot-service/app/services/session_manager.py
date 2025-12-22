# app/services/session_manager.py
import redis
import json
import uuid
from typing import Optional
from app.config import settings
from app.models.agent_state import AgentState, AgentType

class SessionManager:
    """Quản lý session và state của conversations"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.ttl = 3600 * 24  # 24 hours
    
    def create_session(self, user_id: str) -> str:
        """Tạo session mới"""
        session_id = str(uuid.uuid4())
        
        # Initialize state
        state = AgentState(
            session_id=session_id,
            user_id=user_id,
            current_agent=AgentType.ROUTER,
            history=[]
        )
        
        # Save to Redis
        self.redis_client.setex(
            f"session:{session_id}",
            self.ttl,
            state.model_dump_json()
        )
        
        return session_id
    
    async def get_state(self, session_id: str) -> AgentState:
        """Lấy state của session"""
        data = self.redis_client.get(f"session:{session_id}")
        
        if not data:
            # Return default state if not found
            return AgentState(
                session_id=session_id,
                user_id="unknown",
                current_agent=AgentType.ROUTER,
                history=[]
            )
        
        return AgentState.model_validate_json(data)
    
    async def save_state(self, session_id: str, state: AgentState):
        """Lưu state của session"""
        self.redis_client.setex(
            f"session:{session_id}",
            self.ttl,
            state.model_dump_json()
        )
    
    async def delete_session(self, session_id: str):
        """Xóa session"""
        self.redis_client.delete(f"session:{session_id}")
    
    def extend_session(self, session_id: str):
        """Gia hạn session"""
        self.redis_client.expire(f"session:{session_id}", self.ttl)


# Singleton instance
session_manager = SessionManager()