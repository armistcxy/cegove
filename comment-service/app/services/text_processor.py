import re
from typing import List
from underthesea import word_tokenize


class VietnameseTextProcessor:
    """Vietnamese text preprocessing for sentiment analysis"""
    
    # Common abbreviations and their expansions
    ABBREVIATIONS = {
        'ko': 'không',
        'k': 'không',
        'hok': 'không',
        'cx': 'cũng',
        'dc': 'được',
        'đc': 'được',
        'vs': 'với',
        'trc': 'trước',
        'oke': 'ok',
        'okie': 'ok',
        'tks': 'cảm ơn',
        'thks': 'cảm ơn',
        'camon': 'cảm ơn',
        'uk': 'ừ',
        'uh': 'ừ',
        'ntn': 'như thế nào',
        'sao': 'sao',
        'tl': 'trả lời',
        'rep': 'trả lời',
        'nc': 'nói chuyện',
        'wa': 'quá',
        'qá': 'quá',
        'wá': 'quá',
        'r': 'rồi',
        'nha': 'nhé',
        'nhaa': 'nhé',
        'nè': 'này',
        'zai': 'giai',
        'zậy': 'vậy',
        'ny': 'này'
    }
    
    # Teen code patterns
    TEEN_CODE_PATTERNS = {
        r'\bz\b': 'gi',
        r'\bd\b': 'đi',
        r'\bj\b': 'gì',
        r'\bm\b': 'mình',
        r'\bt\b': 'tôi',
        r'\bc\b': 'chị',
        r'\ba\b': 'anh'
    }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Vietnamese text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep Vietnamese
        text = re.sub(r'[^\w\s\u00C0-\u1EF9]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Replace teen code
        for pattern, replacement in VietnameseTextProcessor.TEEN_CODE_PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        
        # Expand abbreviations
        words = text.split()
        expanded_words = [
            VietnameseTextProcessor.ABBREVIATIONS.get(word, word) 
            for word in words
        ]
        text = ' '.join(expanded_words)
        
        # Remove repeated characters (e.g., "hayyyyy" -> "hay")
        text = re.sub(r'(.)\1{2,}', r'\1', text)
        
        return text
    
    @staticmethod
    def word_segment(text: str) -> str:
        """Word segmentation using underthesea"""
        try:
            # Normalize first
            normalized = VietnameseTextProcessor.normalize_text(text)
            
            # Word tokenization
            segmented = word_tokenize(normalized, format="text")
            
            return segmented
        except Exception as e:
            print(f"Error in word segmentation: {e}")
            return text
    
    @staticmethod
    def batch_process(texts: List[str]) -> List[str]:
        """Process multiple texts"""
        return [VietnameseTextProcessor.word_segment(text) for text in texts]