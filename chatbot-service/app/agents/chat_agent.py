# app/agents/chat_agent.py
from typing import Dict, Any, List
from datetime import datetime
import json

from app.services.llm_service import llm_service
from app.tools.movie_tools import MOVIE_TOOLS, execute_tool, get_today_date
from app.models.agent_state import ConversationState
from app.models.chat import ChatMetadata, QuickReplyChip

SYSTEM_PROMPT = f"""You are a friendly movie ticket booking assistant for Cegove Cinema. Today is {get_today_date()}.

Your capabilities:
- Search and recommend movies
- Show movie details and showtimes
- Help users find cinemas
- Guide users to book tickets

Guidelines:
1. Be conversational and helpful. Respond in the same language the user uses (Vietnamese or English).
2. Keep responses short (2-3 sentences). The frontend will show clickable options.
3. Always use tools to get real data - never make up movie names or showtimes.
4. When user clicks a chip (provided in chip_data), use that context to continue.

Date handling:
- "hom nay" / "today" = {get_today_date()}
- "ngay mai" / "tomorrow" = tomorrow's date
- Use YYYY-MM-DD format for date parameters

When user selects a showtime, they will be redirected to the seat selection page.
"""


class ChatAgent:
    """Chat agent using Groq LLM with tool calling."""

    def __init__(self):
        self.tools = MOVIE_TOOLS

    async def process(
        self,
        message: str,
        state: ConversationState,
        chip_data: Dict = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Process user message with LLM + tools.
        Returns response text and structured metadata.
        """
        # Build message with chip context if clicked
        user_content = message
        if chip_data:
            chip_context = f"\n[User clicked: {json.dumps(chip_data, ensure_ascii=False)}]"
            user_content = message + chip_context

        # Build messages for LLM
        messages = state.get_recent_history(10)
        messages.append({"role": "user", "content": user_content})

        try:
            response = llm_service.chat_with_tools(
                messages=messages,
                tools=self.tools,
                system_prompt=SYSTEM_PROMPT
            )
        except Exception as e:
            print(f"[ChatAgent] Error calling LLM: {e}")
            return {
                "response": "Xin loi, toi gap su co ky thuat. Vui long thu lai.",
                "agent": "chat",
                "metadata": ChatMetadata()
            }

        # Process response - handle tool calls (OpenAI format)
        all_chips = []
        choice = response.choices[0]
        response_message = choice.message

        # Check if there are tool calls
        if response_message.tool_calls:
            tool_results = []

            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except:
                    tool_args = {}

                # Execute the tool
                result = await execute_tool(tool_name, tool_args)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "result": result
                })

                # Collect chips from tool result
                if result.get("chips"):
                    all_chips.extend(result["chips"])

            # Build follow-up messages with tool results
            messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in response_message.tool_calls
                ]
            })

            # Add tool results
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": json.dumps(tr["result"]["data"], ensure_ascii=False, default=str)
                })

            # Get final response
            try:
                final_response = llm_service.chat_with_tools(
                    messages=messages,
                    tools=self.tools,
                    system_prompt=SYSTEM_PROMPT
                )
                final_text = final_response.choices[0].message.content or ""
            except Exception as e:
                print(f"[ChatAgent] Error in follow-up call: {e}")
                final_text = "Da tim thay thong tin cho ban."
        else:
            # No tools called - direct response
            final_text = response_message.content or ""

        # Build metadata with chips
        metadata = ChatMetadata(
            chips=[QuickReplyChip(**chip) for chip in all_chips]
        )

        # Update state with this exchange
        state.add_message("user", message)
        state.add_message("assistant", final_text)

        return {
            "response": final_text,
            "agent": "chat",
            "metadata": metadata
        }


# Singleton instance
chat_agent = ChatAgent()
