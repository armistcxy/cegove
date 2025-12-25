# app/services/llm_service.py
from groq import Groq
from typing import List, Dict, Any
from app.config import settings


class LLMService:
    """Groq API wrapper for chat completions with tool use."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-120b"

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        system_prompt: str
    ) -> Any:
        """
        Send messages to LLM with tool definitions.
        Returns response with possible tool_call blocks.
        """
        # Build messages with system prompt
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=2048
        )
        return response

    def chat(
        self,
        messages: List[Dict],
        system_prompt: str
    ) -> Any:
        """Simple chat without tools."""
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=2048
        )
        return response


llm_service = LLMService()
