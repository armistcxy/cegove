import google.generativeai as genai
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import json
from datetime import datetime
import time

from app.models.comment import Comment
from app.models.sentiment import AIInsight
from app.config import settings


class AIInsightService:
    """Service for generating AI insights using Gemini"""
    
    def __init__(self):
        # Configure Gemini API
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
        
        # System prompt
        self.system_instruction = """Bạn là một chuyên gia phân tích đánh giá phim, nhiệm vụ của bạn là đọc một tập bình luận và tạo ra bản mô tả khách quan, dễ hiểu, phục vụ cho hệ thống đặt vé xem phim. Hãy mô tả trung thực dựa trên dữ liệu, tuyệt đối không bịa đặt."""
    
    def _build_prompt(self, comments: List[str], context: Optional[str] = None) -> str:
        """Build prompt from comments"""
        comments_text = "\n".join([f"- {comment}" for comment in comments])
        
        context_text = ""
        if context == "movie":
            context_text = "về bộ phim"
        elif context == "theater":
            context_text = "về rạp chiếu phim"
        
        prompt = f"""Dưới đây là danh sách các bình luận của người xem {context_text}:  
{comments_text}

Hãy phân tích và trả kết quả theo đúng cấu trúc JSON sau:

{{
  "summary": "Tóm tắt tổng quan trong 2-3 câu, nêu cảm nhận chung của đa số khán giả",
  "positive_aspects": [
    "Điểm được khen thứ nhất",
    "Điểm được khen thứ hai"
  ],
  "negative_aspects": [
    "Điểm bị chê thứ nhất",
    "Điểm bị chê thứ hai"
  ],
  "recommendations": "Gợi ý cho người xem: phù hợp với ai, nên kỳ vọng điều gì, ai có thể sẽ không thích"
}}

Lưu ý:
- Trả về ĐÚNG format JSON như trên
- Văn phong tự nhiên, khách quan, không PR
- Chỉ dựa vào bình luận thực tế, không bịa đặt
- Nếu ít bình luận chê, nêu rõ "thiểu số ý kiến"
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> dict:
        """Parse AI response to structured data"""
        try:
            # Try to extract JSON from response
            # Gemini sometimes wraps JSON in markdown code blocks
            if "```json" in response_text:
                # Extract JSON from markdown
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(json_text)
            
            return {
                'summary': data.get('summary', ''),
                'positive_aspects': data.get('positive_aspects', []),
                'negative_aspects': data.get('negative_aspects', []),
                'recommendations': data.get('recommendations', '')
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
            print(f"Response text: {response_text}")
            
            # Fallback: return generic response
            return {
                'summary': 'Không thể tạo tóm tắt do lỗi xử lý dữ liệu.',
                'positive_aspects': [],
                'negative_aspects': [],
                'recommendations': 'Vui lòng xem các bình luận chi tiết để có đánh giá chính xác.'
            }
    
    def generate_insight(
        self,
        db: Session,
        target_type: str,
        target_id: int,
        force_refresh: bool = False,
        max_comments: int = 50
    ) -> Optional[AIInsight]:
        """
        Generate AI insight for a target
        
        Args:
            max_comments: Số lượng comments tối đa để phân tích (để kiểm soát chi phí API)
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")
        
        # Check existing insight
        existing = db.query(AIInsight).filter(
            AIInsight.target_type == target_type,
            AIInsight.target_id == target_id
        ).first()
        
        if existing and not force_refresh and not existing.is_stale:
            return existing
        
        # Get comments
        comments = db.query(Comment).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_approved == True
        ).order_by(Comment.created_at.desc()).limit(max_comments).all()
        
        if not comments or len(comments) < 3:
            # Not enough comments for meaningful analysis
            return None
        
        # Prepare comment texts
        comment_texts = [c.content for c in comments]
        
        # Build prompt
        prompt = self._build_prompt(comment_texts, context=target_type)
        
        try:
            # Call Gemini API
            print(f"🤖 Calling Gemini API for {target_type}/{target_id}...")
            
            response = self.model.generate_content(
                f"{self.system_instruction}\n\n{prompt}",
                generation_config={
                    'temperature': 0.3,  # Lower temperature for more consistent output
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            
            # Parse response
            parsed_data = self._parse_ai_response(response.text)
            
            # Convert lists to JSON strings for storage
            positive_json = json.dumps(parsed_data['positive_aspects'], ensure_ascii=False)
            negative_json = json.dumps(parsed_data['negative_aspects'], ensure_ascii=False)
            
            # Create or update insight
            if existing:
                existing.summary = parsed_data['summary']
                existing.positive_aspects = positive_json
                existing.negative_aspects = negative_json
                existing.recommendations = parsed_data['recommendations']
                existing.based_on_comments = len(comments)
                existing.is_stale = False
                existing.updated_at = datetime.now()
                
                db.commit()
                db.refresh(existing)
                return existing
            else:
                insight = AIInsight(
                    target_type=target_type,
                    target_id=target_id,
                    summary=parsed_data['summary'],
                    positive_aspects=positive_json,
                    negative_aspects=negative_json,
                    recommendations=parsed_data['recommendations'],
                    based_on_comments=len(comments),
                    model_used="gemini-pro",
                    is_stale=False
                )
                
                db.add(insight)
                db.commit()
                db.refresh(insight)
                
                print(f"✅ AI insight generated for {target_type}/{target_id}")
                return insight
                
        except Exception as e:
            print(f"❌ Error generating AI insight: {e}")
            return None
    
    def mark_insight_as_stale(self, db: Session, target_type: str, target_id: int):
        """Mark insight as stale when new comment is added"""
        insight = db.query(AIInsight).filter(
            AIInsight.target_type == target_type,
            AIInsight.target_id == target_id
        ).first()
        
        if insight:
            insight.is_stale = True
            db.commit()
    
    # ==================== TEST METHOD ====================
    
    def test_generate_insight(
        self,
        comments: List[str],
        context: Optional[str] = None,
        sentiment_service = None
    ) -> Dict:
        """
        Test AI insight generation with custom comments (no database)
        
        Args:
            comments: List of comment texts
            context: 'movie' or 'theater' (optional)
            sentiment_service: SentimentService instance for sentiment analysis
        
        Returns:
            Dict with AI insights + sentiment analysis
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")
        
        if len(comments) < 3:
            raise ValueError("Need at least 3 comments for meaningful analysis")
        
        start_time = time.time()
        
        # Analyze sentiment if service provided
        sentiment_results = None
        if sentiment_service:
            sentiment_results = sentiment_service.analyzer.predict_batch(comments)
            
            # Calculate distribution
            positive_count = sum(1 for r in sentiment_results if r['label'] == 'positive')
            neutral_count = sum(1 for r in sentiment_results if r['label'] == 'neutral')
            negative_count = sum(1 for r in sentiment_results if r['label'] == 'negative')
            
            avg_score = sum(r['score'] for r in sentiment_results) / len(sentiment_results)
        else:
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            avg_score = 0.0
        
        # Build prompt
        prompt = self._build_prompt(comments, context)
        
        try:
            # Call Gemini API
            print(f"🤖 Calling Gemini API for test analysis...")
            
            response = self.model.generate_content(
                f"{self.system_instruction}\n\n{prompt}",
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            
            # Parse response
            parsed_data = self._parse_ai_response(response.text)
            
            processing_time = time.time() - start_time
            
            return {
                'total_comments_analyzed': len(comments),
                'sentiment_distribution': {
                    'positive': positive_count,
                    'neutral': neutral_count,
                    'negative': negative_count
                },
                'average_sentiment_score': round(avg_score, 2),
                'summary': parsed_data['summary'],
                'positive_aspects': parsed_data['positive_aspects'],
                'negative_aspects': parsed_data['negative_aspects'],
                'recommendations': parsed_data['recommendations'],
                'model_used': 'gemini-pro',
                'processing_time_seconds': round(processing_time, 2)
            }
            
        except Exception as e:
            raise Exception(f"Error generating test insight: {str(e)}")