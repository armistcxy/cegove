from fastapi import APIRouter, HTTPException, Depends
from app.models.chat import ChatMessage, ChatResponse
from app.services.session_manager import SessionManager
from app.agents.router_agent import RouterAgent
from app.api.deps import get_current_user
from datetime import datetime
from typing import Optional

router = APIRouter()

# Khởi tạo dependencies
session_manager = SessionManager()
router_agent = RouterAgent()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    Xử lý tin nhắn chat từ người dùng
    
    Authentication: Bearer token required (JWT)
    - Token phải chứa userId từ AuthService
    
    Flow:
    1. Lấy user_id từ JWT token (đã xác thực)
    2. Lấy hoặc tạo session
    3. Load conversation state
    4. Router agent phân tích và route đến agent phù hợp
    5. Agent xử lý và trả response
    6. Lưu state và history
    """
    try:
        # Get authenticated user_id from JWT token (convert to string)
        user_id = str(current_user["user_id"])
        
        # 1. Get or create session
        session_id = message.session_id or session_manager.create_session(user_id)
        
        # 2. Load state
        state = await session_manager.get_state(session_id)
        
        # Save user message immediately
        state.history.append({
            "role": "user",
            "content": message.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 3. Process through router
        result = await router_agent.process(message.message, state)
        
        # 4. Update state with assistant response
        state.history.append({
            "role": "assistant",
            "content": result["response"],
            "agent": result["agent"],
            "timestamp": datetime.now().isoformat()
        })
        
        # 5. Save state
        await session_manager.save_state(session_id, state)
        
        # 6. Return response
        return ChatResponse(
            session_id=session_id,
            message=result["response"],
            agent=result["agent"],
            timestamp=datetime.now(),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        # Save error state if session exists
        if 'session_id' in locals() and 'state' in locals():
            try:
                state.history.append({
                    "role": "system",
                    "content": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
                await session_manager.save_state(session_id, state)
            except:
                pass  # Don't fail on save error
        
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/{session_id}/history")
async def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)  # Tạm comment để test
):
    """Lấy lịch sử chat của session"""
    state = await session_manager.get_state(session_id)
    return {"session_id": session_id, "history": state.history}

@router.delete("/chat/{session_id}")
async def clear_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)  # Tạm comment để test
):
    """Xóa session"""
    await session_manager.delete_session(session_id)
    return {"message": "Session cleared successfully"}