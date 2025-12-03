import torch
from transformers import RobertaForSequenceClassification, AutoTokenizer
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import numpy as np
from datetime import datetime

from app.models.comment import Comment
from app.models.sentiment import SentimentScore, CommentSentiment
from app.services.text_processor import VietnameseTextProcessor


class SentimentAnalyzer:
    """Singleton pattern for PhoBERT model"""
    
    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_model()
        return cls._instance
    
    def _initialize_model(self):
        """Initialize PhoBERT model once"""
        print("Loading PhoBERT sentiment model...")
        
        try:
            self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"Using device: {self._device}")
            
            model_name = "wonrax/phobert-base-vietnamese-sentiment"
            
            self._model = RobertaForSequenceClassification.from_pretrained(model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
            
            self._model.to(self._device)
            self._model.eval()
            
            print("PhoBERT model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def predict_sentiment(self, text: str) -> Dict[str, float]:
        """
        Predict sentiment for a single text
        
        Returns:
            {
                'negative': float,
                'positive': float,
                'neutral': float,
                'score': float (0-5),
                'label': str
            }
        """
        try:
            # Preprocess and segment
            processed_text = VietnameseTextProcessor.word_segment(text)
            
            # Tokenize
            input_ids = torch.tensor([self._tokenizer.encode(processed_text)])
            input_ids = input_ids.to(self._device)
            
            # Predict
            with torch.no_grad():
                output = self._model(input_ids)
                probabilities = output.logits.softmax(dim=-1).tolist()[0]
            
            neg_prob, pos_prob, neu_prob = probabilities
            
            # Calculate score (0-5 scale)
            score = (pos_prob * 5.0) + (neu_prob * 2.5) + (neg_prob * 0.0)
            
            # Determine label
            max_prob = max(neg_prob, pos_prob, neu_prob)
            if max_prob == pos_prob:
                label = 'positive'
            elif max_prob == neu_prob:
                label = 'neutral'
            else:
                label = 'negative'
            
            return {
                'negative': round(neg_prob, 4),
                'positive': round(pos_prob, 4),
                'neutral': round(neu_prob, 4),
                'score': round(score, 2),
                'label': label,
                'processed_text': processed_text
            }
            
        except Exception as e:
            print(f"Error in sentiment prediction: {e}")
            # Return neutral on error
            return {
                'negative': 0.33,
                'positive': 0.33,
                'neutral': 0.34,
                'score': 2.5,
                'label': 'neutral',
                'processed_text': text
            }
    
    def predict_batch(self, texts: List[str], batch_size: int = 16) -> List[Dict[str, float]]:
        """
        Predict sentiment for multiple texts in batches
        More efficient than processing one by one
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Preprocess all texts in batch
            processed_texts = VietnameseTextProcessor.batch_process(batch_texts)
            
            # Tokenize batch
            encodings = self._tokenizer(
                processed_texts,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors='pt'
            )
            
            input_ids = encodings['input_ids'].to(self._device)
            attention_mask = encodings['attention_mask'].to(self._device)
            
            # Predict batch
            with torch.no_grad():
                outputs = self._model(input_ids, attention_mask=attention_mask)
                probabilities = outputs.logits.softmax(dim=-1).cpu().numpy()
            
            # Process results
            for j, (probs, processed_text) in enumerate(zip(probabilities, processed_texts)):
                neg_prob, pos_prob, neu_prob = probs
                
                score = (pos_prob * 5.0) + (neu_prob * 2.5) + (neg_prob * 0.0)
                
                max_prob = max(neg_prob, pos_prob, neu_prob)
                if max_prob == pos_prob:
                    label = 'positive'
                elif max_prob == neu_prob:
                    label = 'neutral'
                else:
                    label = 'negative'
                
                results.append({
                    'negative': round(float(neg_prob), 4),
                    'positive': round(float(pos_prob), 4),
                    'neutral': round(float(neu_prob), 4),
                    'score': round(float(score), 2),
                    'label': label,
                    'processed_text': processed_text
                })
        
        return results


class SentimentService:
    """Service for sentiment analysis and scoring"""
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
    
    def analyze_comment(self, db: Session, comment_id: int) -> Optional[CommentSentiment]:
        """Analyze sentiment for a single comment"""
        # Check if already analyzed
        existing = db.query(CommentSentiment).filter(
            CommentSentiment.comment_id == comment_id
        ).first()
        
        if existing:
            return existing
        
        # Get comment
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return None
        
        # Analyze
        result = self.analyzer.predict_sentiment(comment.content)
        
        # Save to database
        sentiment = CommentSentiment(
            comment_id=comment_id,
            positive_prob=result['positive'],
            neutral_prob=result['neutral'],
            negative_prob=result['negative'],
            sentiment_score=result['score'],
            sentiment_label=result['label'],
            processed_text=result['processed_text']
        )
        
        db.add(sentiment)
        db.commit()
        db.refresh(sentiment)
        
        return sentiment
    
    def calculate_target_score(
        self,
        db: Session,
        target_type: str,
        target_id: int,
        force_refresh: bool = False
    ) -> SentimentScore:
        """
        Calculate overall sentiment score for a target (movie/theater)
        Uses cached results if available and not stale
        """
        # Check existing score
        existing = db.query(SentimentScore).filter(
            SentimentScore.target_type == target_type,
            SentimentScore.target_id == target_id
        ).first()
        
        if existing and not force_refresh and not existing.is_stale:
            return existing
        
        # Get all approved comments for target
        comments = db.query(Comment).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_approved == True
        ).all()
        
        if not comments:
            # No comments, return neutral score
            score_data = {
                'target_type': target_type,
                'target_id': target_id,
                'average_score': 2.5,
                'total_comments': 0,
                'positive_count': 0,
                'neutral_count': 0,
                'negative_count': 0,
                'avg_positive_prob': 0.0,
                'avg_neutral_prob': 0.0,
                'avg_negative_prob': 0.0,
                'is_stale': False
            }
            
            if existing:
                for key, value in score_data.items():
                    setattr(existing, key, value)
                db.commit()
                return existing
            else:
                new_score = SentimentScore(**score_data)
                db.add(new_score)
                db.commit()
                db.refresh(new_score)
                return new_score
        
        # Batch analyze comments
        comment_texts = [c.content for c in comments]
        comment_ids = [c.id for c in comments]
        
        results = self.analyzer.predict_batch(comment_texts)
        
        # Save individual sentiments
        for comment_id, result in zip(comment_ids, results):
            # Check if already exists
            existing_sentiment = db.query(CommentSentiment).filter(
                CommentSentiment.comment_id == comment_id
            ).first()
            
            if not existing_sentiment:
                sentiment = CommentSentiment(
                    comment_id=comment_id,
                    positive_prob=result['positive'],
                    neutral_prob=result['neutral'],
                    negative_prob=result['negative'],
                    sentiment_score=result['score'],
                    sentiment_label=result['label'],
                    processed_text=result['processed_text']
                )
                db.add(sentiment)
        
        db.commit()
        
        # Calculate aggregated scores
        scores = [r['score'] for r in results]
        labels = [r['label'] for r in results]
        
        avg_score = np.mean(scores)
        positive_count = labels.count('positive')
        neutral_count = labels.count('neutral')
        negative_count = labels.count('negative')
        
        avg_pos_prob = np.mean([r['positive'] for r in results])
        avg_neu_prob = np.mean([r['neutral'] for r in results])
        avg_neg_prob = np.mean([r['negative'] for r in results])
        
        score_data = {
            'target_type': target_type,
            'target_id': target_id,
            'average_score': round(float(avg_score), 2),
            'total_comments': len(comments),
            'positive_count': positive_count,
            'neutral_count': neutral_count,
            'negative_count': negative_count,
            'avg_positive_prob': round(float(avg_pos_prob), 4),
            'avg_neutral_prob': round(float(avg_neu_prob), 4),
            'avg_negative_prob': round(float(avg_neg_prob), 4),
            'is_stale': False,
            'last_calculated_at': datetime.now()
        }
        
        if existing:
            for key, value in score_data.items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_score = SentimentScore(**score_data)
            db.add(new_score)
            db.commit()
            db.refresh(new_score)
            return new_score
    
    def mark_target_as_stale(self, db: Session, target_type: str, target_id: int):
        """Mark target score as stale when new comment is added"""
        score = db.query(SentimentScore).filter(
            SentimentScore.target_type == target_type,
            SentimentScore.target_id == target_id
        ).first()
        
        if score:
            score.is_stale = True
            db.commit()