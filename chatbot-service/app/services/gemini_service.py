# app/services/gemini_service.py
import google.generativeai as genai
from app.config import settings
from typing import List, Dict, Any, Optional
import json
import time

class GeminiService:
    """Service để tương tác với Gemini API - Simple wrapper"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def create_model(self, system_instruction: Optional[str] = None):
        """Create a new Gemini model instance"""
        if system_instruction:
            return genai.GenerativeModel(
                'gemini-2.0-flash',
                system_instruction=system_instruction
            )
        return genai.GenerativeModel('gemini-2.0-flash')


# Singleton instance
gemini_service = GeminiService()