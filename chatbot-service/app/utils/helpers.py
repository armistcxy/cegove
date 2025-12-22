# app/utils/helpers.py
from datetime import datetime
from typing import Optional

def format_currency(amount: float) -> str:
    """Format currency to VND"""
    return f"{amount:,.0f} VNĐ"

def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string"""
    return dt.strftime("%d/%m/%Y %H:%M")

def extract_numbers(text: str) -> Optional[int]:
    """Extract first number from text"""
    import re
    numbers = re.findall(r'\d+', text)
    return int(numbers[0]) if numbers else None

def is_positive_response(text: str) -> bool:
    """Check if text is a positive response"""
    positive_words = ["có", "yes", "ok", "được", "đồng ý", "xác nhận", "oke", "okie"]
    return any(word in text.lower() for word in positive_words)

def is_negative_response(text: str) -> bool:
    """Check if text is a negative response"""
    negative_words = ["không", "no", "thôi", "hủy", "cancel", "bỏ"]
    return any(word in text.lower() for word in negative_words)