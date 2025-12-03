from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.sentiment import (
    SentimentPrediction, TargetSentimentScore,
    TextProcessRequest, TextProcessResponse,
    BatchSentimentRequest, BatchSentimentResponse,
    CommentSentimentResponse
)
from app.services.sentiment_service import SentimentService
from app.services.text_processor import VietnameseTextProcessor
from app.api.v1.deps import get_current_user, require_admin

router = APIRouter()
sentiment_service = SentimentService()


@router.post("/test/predict", response_model=SentimentPrediction)
def test_sentiment_prediction(
    text: str = Query(..., min_length=1, max_length=2000, description="Text to analyze")
):
    """
    **TEST ENDPOINT** - Predict sentiment for a single text
    
    Returns raw model output with probabilities [NEG, POS, NEU]
    
    Example:
    - Input: "Phim rất hay và cảm động"
    - Output: {"negative": 0.002, "positive": 0.988, "neutral": 0.01, "score": 4.94, "label": "positive"}
    """
    result = sentiment_service.analyzer.predict_sentiment(text)
    return SentimentPrediction(**result)


@router.post("/test/process", response_model=TextProcessResponse)
def test_text_processing(request: TextProcessRequest):
    """
    **TEST ENDPOINT** - Test Vietnamese text preprocessing
    
    Shows each step: normalization and word segmentation
    """
    normalized = VietnameseTextProcessor.normalize_text(request.text)
    segmented = VietnameseTextProcessor.word_segment(request.text)
    
    return TextProcessResponse(
        original_text=request.text,
        normalized_text=normalized,
        segmented_text=segmented
    )


@router.post("/test/batch", response_model=BatchSentimentResponse)
def test_batch_prediction(request: BatchSentimentRequest):
    """
    **TEST ENDPOINT** - Batch sentiment prediction
    
    Analyze multiple texts at once (more efficient than individual calls)
    """
    results = sentiment_service.analyzer.predict_batch(request.texts)
    
    return BatchSentimentResponse(
        results=[SentimentPrediction(**r) for r in results],
        total_processed=len(results)
    )


@router.get("/score/{target_type}/{target_id}", response_model=TargetSentimentScore)
def get_target_sentiment_score(
    target_type: str,
    target_id: int,
    force_refresh: bool = Query(False, description="Force recalculation"),
    db: Session = Depends(get_db)
):
    """
    **PUBLIC** - Get overall sentiment score for a movie or theater
    
    Returns:
    - Average score (0-5 scale)
    - Sentiment distribution (positive/neutral/negative counts)
    - Probability averages
    
    Uses cached results for performance. Set force_refresh=true to recalculate.
    """
    if target_type not in ["movie", "theater"]:
        raise HTTPException(status_code=400, detail="Invalid target_type")
    
    try:
        score = sentiment_service.calculate_target_score(
            db=db,
            target_type=target_type,
            target_id=target_id,
            force_refresh=force_refresh
        )
        
        return TargetSentimentScore(
            target_type=score.target_type,
            target_id=score.target_id,
            average_score=score.average_score,
            total_comments=score.total_comments,
            positive_count=score.positive_count,
            neutral_count=score.neutral_count,
            negative_count=score.negative_count,
            avg_positive_prob=score.avg_positive_prob,
            avg_neutral_prob=score.avg_neutral_prob,
            avg_negative_prob=score.avg_negative_prob,
            last_calculated_at=score.last_calculated_at,
            is_stale=score.is_stale
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating sentiment: {str(e)}")


@router.post("/score/{target_type}/{target_id}/refresh", response_model=TargetSentimentScore)
def refresh_target_sentiment(
    target_type: str,
    target_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    **ADMIN ONLY** - Force refresh sentiment score for a target
    
    Recalculates sentiment from all comments.
    Can be run in background for large datasets.
    """
    if target_type not in ["movie", "theater"]:
        raise HTTPException(status_code=400, detail="Invalid target_type")
    
    # Refresh in background
    def refresh_task():
        sentiment_service.calculate_target_score(
            db=db,
            target_type=target_type,
            target_id=target_id,
            force_refresh=True
        )
    
    background_tasks.add_task(refresh_task)
    
    # Return current score
    score = db.query(SentimentScore).filter(
        SentimentScore.target_type == target_type,
        SentimentScore.target_id == target_id
    ).first()
    
    if not score:
        raise HTTPException(status_code=404, detail="Score not found. Will be calculated in background.")
    
    return TargetSentimentScore.from_orm(score)


@router.get("/comment/{comment_id}", response_model=CommentSentimentResponse)
def get_comment_sentiment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    **PUBLIC** - Get sentiment analysis for a specific comment
    """
    sentiment = sentiment_service.analyze_comment(db, comment_id)
    
    if not sentiment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return CommentSentimentResponse(
        comment_id=sentiment.comment_id,
        sentiment=SentimentPrediction(
            negative=sentiment.negative_prob,
            positive=sentiment.positive_prob,
            neutral=sentiment.neutral_prob,
            score=sentiment.sentiment_score,
            label=sentiment.sentiment_label,
            processed_text=sentiment.processed_text
        ),
        created_at=sentiment.created_at
    )


@router.post("/admin/recalculate-all")
def recalculate_all_scores(
    background_tasks: BackgroundTasks,
    target_type: Optional[str] = Query(None, pattern="^(movie|theater)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    **ADMIN ONLY** - Recalculate all sentiment scores
    
    Warning: This can be time-consuming for large datasets.
    Runs in background.
    """
    def recalculate_all():
        # Get all unique targets
        from app.models.comment import Comment
        
        query = db.query(Comment.target_type, Comment.target_id).distinct()
        
        if target_type:
            query = query.filter(Comment.target_type == target_type)
        
        targets = query.all()
        
        for t_type, t_id in targets:
            try:
                sentiment_service.calculate_target_score(
                    db=db,
                    target_type=t_type,
                    target_id=t_id,
                    force_refresh=True
                )
            except Exception as e:
                print(f"Error calculating score for {t_type}/{t_id}: {e}")
    
    background_tasks.add_task(recalculate_all)
    
    return {"message": "Recalculation started in background"}