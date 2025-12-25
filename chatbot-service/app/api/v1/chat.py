# app/api/v1/chat.py
from fastapi import APIRouter, HTTPException, Depends
from app.models.chat import ChatMessage, ChatResponse
from app.services.session_manager import session_manager
from app.agents.chat_agent import chat_agent
from app.api.deps import get_current_user
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process chat message from user using Claude agent.

    Flow:
    1. Get or create session
    2. Load conversation state
    3. Process with Claude agent (handles NLU + tool calling)
    4. Save state
    5. Return response with structured metadata
    """
    try:
        user_id = message.user_id

        # 1. Get or create session
        session_id = message.session_id or session_manager.create_session(user_id)

        # 2. Load state
        state = await session_manager.get_state(session_id)

        # 3. Process with chat agent
        result = await chat_agent.process(
            message=message.message,
            state=state,
            chip_data=message.chip_data,
            user_id=user_id
        )

        # 4. Save state (history is updated by agent)
        await session_manager.save_state(session_id, state)

        # 5. Return response
        return ChatResponse(
            session_id=session_id,
            message=result["response"],
            agent=result["agent"],
            timestamp=datetime.now(),
            metadata=result.get("metadata")
        )

    except Exception as e:
        print(f"[chat] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}/history")
async def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get chat history for session."""
    state = await session_manager.get_state(session_id)
    return {"session_id": session_id, "history": state.history}


@router.delete("/chat/{session_id}")
async def clear_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete session."""
    await session_manager.delete_session(session_id)
    return {"message": "Session cleared successfully"}
