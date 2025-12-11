# comment-service/app/services/comment_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta

from app.models.comment import Comment, CommentLike, CommentReport
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentService:
    
    @staticmethod
    def create_comment(
        db: Session,
        comment_data: CommentCreate,
        user_id: int,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Comment:
        """Create new comment"""
        comment = Comment(
            user_id=user_id,
            target_type=comment_data.target_type,
            target_id=comment_data.target_id,
            content=comment_data.content,
            rating=comment_data.rating,  # Add rating here
            user_name=user_name,
            user_email=user_email,
            is_approved=True
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        # Mark sentiment as stale
        from app.services.sentiment_service import SentimentService
        sentiment_service = SentimentService()
        sentiment_service.mark_target_as_stale(
            db, comment.target_type, comment.target_id
        )
        
        # Mark AI insight as stale
        from app.services.ai_insight_service import AIInsightService
        ai_service = AIInsightService()
        ai_service.mark_insight_as_stale(
            db, comment.target_type, comment.target_id
        )
        
        return comment
    
    @staticmethod
    def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def update_comment(
        db: Session,
        comment_id: int,
        comment_data: CommentUpdate,
        user_id: int
    ) -> Optional[Comment]:
        """Update comment (only by owner)"""
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id
        ).first()
        
        if not comment:
            return None
        
        update_data = comment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(comment, field, value)
        
        db.commit()
        db.refresh(comment)
        return comment
    
    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int, is_admin: bool = False) -> bool:
        """Delete comment (by owner or admin)"""
        query = db.query(Comment).filter(Comment.id == comment_id)
        
        if not is_admin:
            query = query.filter(Comment.user_id == user_id)
        
        comment = query.first()
        if not comment:
            return False
        
        db.delete(comment)
        db.commit()
        return True
    
    @staticmethod
    def get_comments_by_target(
        db: Session,
        target_type: str,
        target_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "recent",  # recent, popular
        current_user_id: Optional[int] = None,
        only_approved: bool = True
    ) -> Tuple[List[Dict], int]:
        """
        Get comments for a specific target with pagination
        Returns comments with likes_count and user_has_liked
        """
        query = db.query(
            Comment,
            func.count(CommentLike.id).label('likes_count')
        ).outerjoin(
            CommentLike, Comment.id == CommentLike.comment_id
        ).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id
        ).group_by(Comment.id)
        
        if only_approved:
            query = query.filter(Comment.is_approved == True)
        
        # Apply sorting
        if sort_by == "popular":
            query = query.order_by(desc('likes_count'), desc(Comment.created_at))
        else:  # recent
            query = query.order_by(desc(Comment.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()
        
        # Check if current user has liked each comment
        user_liked_comments = set()
        if current_user_id:
            comment_ids = [comment.id for comment, _ in results]
            likes = db.query(CommentLike.comment_id).filter(
                CommentLike.comment_id.in_(comment_ids),
                CommentLike.user_id == current_user_id
            ).all()
            user_liked_comments = {like[0] for like in likes}
        
        # Build response
        comments_with_stats = []
        for comment, likes_count in results:
            comment_dict = {
                'comment': comment,
                'likes_count': likes_count,
                'user_has_liked': comment.id in user_liked_comments
            }
            comments_with_stats.append(comment_dict)
        
        return comments_with_stats, total
    
    @staticmethod
    def get_user_comments(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        target_type: Optional[str] = None
    ) -> Tuple[List[Comment], int]:
        """Get all comments by a user"""
        query = db.query(Comment).filter(Comment.user_id == user_id)
        
        if target_type:
            query = query.filter(Comment.target_type == target_type)
        
        query = query.order_by(desc(Comment.created_at))
        
        total = query.count()
        offset = (page - 1) * page_size
        comments = query.offset(offset).limit(page_size).all()
        
        return comments, total
    
    @staticmethod
    def like_comment(db: Session, comment_id: int, user_id: int) -> bool:
        """Add like to comment"""
        # Check if already liked
        existing = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id
        ).first()
        
        if existing:
            return False  # Already liked
        
        # Check if comment exists
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return False
        
        like = CommentLike(comment_id=comment_id, user_id=user_id)
        db.add(like)
        db.commit()
        return True
    
    @staticmethod
    def unlike_comment(db: Session, comment_id: int, user_id: int) -> bool:
        """Remove like from comment"""
        like = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id
        ).first()
        
        if not like:
            return False
        
        db.delete(like)
        db.commit()
        return True
    
    @staticmethod
    def report_comment(
        db: Session,
        comment_id: int,
        reporter_user_id: int,
        reason: str,
        description: Optional[str] = None
    ) -> CommentReport:
        """Report a comment"""
        # Check if comment exists
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise ValueError("Comment not found")
        
        # Check if already reported by this user
        existing = db.query(CommentReport).filter(
            CommentReport.comment_id == comment_id,
            CommentReport.reporter_user_id == reporter_user_id,
            CommentReport.status == 'pending'
        ).first()
        
        if existing:
            raise ValueError("You have already reported this comment")
        
        report = CommentReport(
            comment_id=comment_id,
            reporter_user_id=reporter_user_id,
            reason=reason,
            description=description
        )
        
        db.add(report)
        
        # Auto-flag comment if multiple reports
        report_count = db.query(func.count(CommentReport.id)).filter(
            CommentReport.comment_id == comment_id,
            CommentReport.status == 'pending'
        ).scalar()
        
        if report_count >= 3:  # Flag after 3 reports
            comment.is_flagged = True
        
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_statistics(
        db: Session,
        target_type: str,
        target_id: int
    ) -> Dict:
        """Get comment statistics for a target including rating information"""
        # Total comments
        total_comments = db.query(func.count(Comment.id)).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_approved == True
        ).scalar()
        
        # Total likes
        total_likes = db.query(func.count(CommentLike.id)).join(
            Comment, Comment.id == CommentLike.comment_id
        ).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id
        ).scalar()
        
        # Recent comments (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_count = db.query(func.count(Comment.id)).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_approved == True,
            Comment.created_at >= seven_days_ago
        ).scalar()
        
        # Rating statistics
        rating_stats = db.query(
            func.avg(Comment.rating).label('avg_rating'),
            func.count(Comment.rating).label('total_ratings')
        ).filter(
            Comment.target_type == target_type,
            Comment.target_id == target_id,
            Comment.is_approved == True,
            Comment.rating.isnot(None)
        ).first()
        
        average_rating = float(rating_stats.avg_rating) if rating_stats.avg_rating else None
        total_ratings = rating_stats.total_ratings or 0
        
        # Rating distribution (1-5 stars)
        rating_distribution = {}
        for star in range(1, 6):
            count = db.query(func.count(Comment.id)).filter(
                Comment.target_type == target_type,
                Comment.target_id == target_id,
                Comment.is_approved == True,
                Comment.rating >= star,
                Comment.rating < (star + 1)
            ).scalar()
            rating_distribution[str(star)] = count
        
        return {
            'target_type': target_type,
            'target_id': target_id,
            'total_comments': total_comments,
            'total_likes': total_likes,
            'recent_comments_count': recent_count,
            'average_rating': round(average_rating, 2) if average_rating else None,
            'total_ratings': total_ratings,
            'rating_distribution': rating_distribution
        }
    
    # ==================== ADMIN METHODS ====================
    
    @staticmethod
    def get_flagged_comments(
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """Get all flagged comments (admin only)"""
        query = db.query(
            Comment,
            func.count(CommentReport.id).label('reports_count')
        ).outerjoin(
            CommentReport, Comment.id == CommentReport.comment_id
        ).filter(
            Comment.is_flagged == True
        ).group_by(Comment.id).order_by(desc('reports_count'))
        
        total = query.count()
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()
        
        comments_with_reports = []
        for comment, reports_count in results:
            comments_with_reports.append({
                'comment': comment,
                'reports_count': reports_count
            })
        
        return comments_with_reports, total
    
    @staticmethod
    def get_pending_reports(
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CommentReport], int]:
        """Get pending reports (admin only)"""
        query = db.query(CommentReport).filter(
            CommentReport.status == 'pending'
        ).order_by(desc(CommentReport.created_at))
        
        total = query.count()
        offset = (page - 1) * page_size
        reports = query.offset(offset).limit(page_size).all()
        
        return reports, total
    
    @staticmethod
    def update_comment_moderation(
        db: Session,
        comment_id: int,
        is_approved: Optional[bool] = None,
        is_flagged: Optional[bool] = None
    ) -> Optional[Comment]:
        """Update comment moderation status (admin only)"""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return None
        
        if is_approved is not None:
            comment.is_approved = is_approved
        if is_flagged is not None:
            comment.is_flagged = is_flagged
        
        db.commit()
        db.refresh(comment)
        return comment
    
    @staticmethod
    def resolve_report(
        db: Session,
        report_id: int,
        status: str = 'resolved'
    ) -> Optional[CommentReport]:
        """Resolve a report (admin only)"""
        report = db.query(CommentReport).filter(CommentReport.id == report_id).first()
        if not report:
            return None
        
        report.status = status
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def bulk_delete_comments(
        db: Session,
        comment_ids: List[int]
    ) -> int:
        """Bulk delete comments (admin only)"""
        deleted = db.query(Comment).filter(Comment.id.in_(comment_ids)).delete(synchronize_session=False)
        db.commit()
        return deleted
    
    @staticmethod
    def get_aggregated_stats(db: Session, target_type: Optional[str] = None) -> Dict:
        """Get aggregated statistics across all targets (admin only)"""
        query = db.query(Comment)
        if target_type:
            query = query.filter(Comment.target_type == target_type)
        
        total_comments = query.count()
        approved_comments = query.filter(Comment.is_approved == True).count()
        flagged_comments = query.filter(Comment.is_flagged == True).count()
        
        # Comments per target type
        comments_by_type = db.query(
            Comment.target_type,
            func.count(Comment.id).label('count')
        ).group_by(Comment.target_type).all()
        
        return {
            'total_comments': total_comments,
            'approved_comments': approved_comments,
            'flagged_comments': flagged_comments,
            'comments_by_type': {t: c for t, c in comments_by_type}
        }