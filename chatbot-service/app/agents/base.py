from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.agent_state import AgentState

class BaseAgent(ABC):
    """Base class cho tất cả agents"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, message: str, state: AgentState) -> Dict[str, Any]:
        """
        Xử lý message và trả về response
        
        Args:
            message: Tin nhắn từ user
            state: Trạng thái hiện tại của conversation
            
        Returns:
            Dict chứa response và updated state
        """
        pass
    
    @abstractmethod
    async def can_handle(self, message: str, state: AgentState) -> bool:
        """
        Kiểm tra agent có thể xử lý message này không
        
        Args:
            message: Tin nhắn từ user
            state: Trạng thái hiện tại
            
        Returns:
            True nếu agent có thể xử lý
        """
        pass
