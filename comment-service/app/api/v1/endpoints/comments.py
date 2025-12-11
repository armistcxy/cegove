# comment-service/app/api/v1/endpoints/comments.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from app.database import get_db
from app.schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse,
    PaginatedCommentsResponse, CommentStatistics,
    CommentReportCreate, CommentReportResponse,
    CommentModerationUpdate, BulkCommentAction,
    CommentWithStats
)
from app.services.comment_service import CommentService
from app.api.v1.deps import get_current_user, require_admin

router = APIRouter()


# ==================== PUBLIC & USER ENDPOINTS ====================

@router.get("/target/{target_type}/{target_id}", response_model=PaginatedCommentsResponse)
def get_comments_by_target(
    target_type: str,
    target_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("recent", pattern="^(recent|popular)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comments for a movie or theater
    
    **Authentication optional** - Shows like status if authenticated
    
    - **target_type**: 'movie' or 'theater'
    - **target_id**: ID of the target
    - **sort_by**: recent or popular (by likes)
    """
    if target_type not in ["movie", "theater"]:
        raise HTTPException(status_code=400, detail="Invalid target_type. Must be 'movie' or 'theater'")
    
    current_user_id = current_user.get("user_id") if current_user else None
    
    comments_with_stats, total = CommentService.get_comments_by_target(
        db=db,
        target_type=target_type,
        target_id=target_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        current_user_id=current_user_id
    )
    
    # Build response items
    items = []
    for item in comments_with_stats:
        comment = item['comment']
        comment_response = CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            user_name=comment.user_name,
            user_email=comment.user_email,
            target_type=comment.target_type,
            target_id=comment.target_id,
            content=comment.content,
            is_approved=comment.is_approved,
            is_flagged=comment.is_flagged,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            likes_count=item['likes_count'],
            user_has_liked=item['user_has_liked']
        )
        items.append(comment_response)
    
    total_pages = math.ceil(total / page_size)
    
    return PaginatedCommentsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/target/{target_type}/{target_id}/stats", response_model=CommentStatistics)
def get_target_statistics(
    target_type: str,
    target_id: int,
    db: Session = Depends(get_db)
    # Public endpoint
):
    """
    Get comment statistics for a movie or theater
    
    **Public endpoint** - No authentication required
    
    Returns total comments, average rating, rating distribution, etc.
    """
    if target_type not in ["movie", "theater"]:
        raise HTTPException(status_code=400, detail="Invalid target_type")
    
    stats = CommentService.get_statistics(db, target_type, target_id)
    return CommentStatistics(**stats)


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new comment
    
    **Authentication required** - Only logged-in users can comment
    
    - Can comment on movies or theaters
    """
    created_comment = CommentService.create_comment(
        db=db,
        comment_data=comment,
        user_id=current_user["user_id"],
        user_name=current_user.get("name"),
        user_email=current_user.get("email")
    )
    
    return CommentResponse(
        id=created_comment.id,
        user_id=created_comment.user_id,
        user_name=created_comment.user_name,
        user_email=created_comment.user_email,
        target_type=created_comment.target_type,
        target_id=created_comment.target_id,
        content=created_comment.content,
        is_approved=created_comment.is_approved,
        is_flagged=created_comment.is_flagged,
        created_at=created_comment.created_at,
        updated_at=created_comment.updated_at,
        likes_count=0,
        user_has_liked=False
    )


@router.get("/me", response_model=PaginatedCommentsResponse)
def get_my_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    target_type: Optional[str] = Query(None, pattern="^(movie|theater)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Get my comments
    
    **Authentication required**
    
    Optional filter by target_type
    """
    comments, total = CommentService.get_user_comments(
        db=db,
        user_id=current_user["user_id"],
        page=page,
        page_size=page_size,
        target_type=target_type
    )
    
    items = [
        CommentResponse(
            id=c.id,
            user_id=c.user_id,
            user_name=c.user_name,
            user_email=c.user_email,
            target_type=c.target_type,
            target_id=c.target_id,
            content=c.content,
            rating=c.rating,
            is_approved=c.is_approved,
            is_flagged=c.is_flagged,
            created_at=c.created_at,
            updated_at=c.updated_at,
            likes_count=0,  # Can be computed if needed
            user_has_liked=False
        )
        for c in comments
    ]
    
    total_pages = math.ceil(total / page_size)
    
    return PaginatedCommentsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Optional for user_has_liked
):
    """
    Get comment by ID
    
    **Authentication optional**
    """
    comment = CommentService.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Get likes count
    from app.models.comment import CommentLike
    likes_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
    
    # Check if user has liked
    user_has_liked = False
    if current_user:
        user_like = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == current_user["user_id"]
        ).first()
        user_has_liked = user_like is not None
    
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        user_name=comment.user_name,
        user_email=comment.user_email,
        target_type=comment.target_type,
        target_id=comment.target_id,
        content=comment.content,
        rating=comment.rating,
        is_approved=comment.is_approved,
        is_flagged=comment.is_flagged,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        likes_count=likes_count,
        user_has_liked=user_has_liked
    )


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Update own comment
    
    **Authentication required** - Can only update your own comments
    """
    updated_comment = CommentService.update_comment(
        db=db,
        comment_id=comment_id,
        comment_data=comment_update,
        user_id=current_user["user_id"]
    )
    
    if not updated_comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found or you don't have permission"
        )
    
    return CommentResponse(
        id=updated_comment.id,
        user_id=updated_comment.user_id,
        user_name=updated_comment.user_name,
        user_email=updated_comment.user_email,
        target_type=updated_comment.target_type,
        target_id=updated_comment.target_id,
        content=updated_comment.content,
        is_approved=updated_comment.is_approved,
        is_flagged=updated_comment.is_flagged,
        created_at=updated_comment.created_at,
        updated_at=updated_comment.updated_at,
        likes_count=0,
        user_has_liked=False
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Delete own comment
    
    **Authentication required** - Can only delete your own comments
    """
    success = CommentService.delete_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user["user_id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Comment not found or you don't have permission"
        )
    
    return None


@router.post("/{comment_id}/like", status_code=status.HTTP_201_CREATED)
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Like a comment
    
    **Authentication required**
    """
    success = CommentService.like_comment(db, comment_id, current_user["user_id"])
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Comment not found or already liked"
        )
    
    return {"message": "Comment liked successfully"}


@router.delete("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Unlike a comment
    
    **Authentication required**
    """
    success = CommentService.unlike_comment(db, comment_id, current_user["user_id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="Like not found")
    
    return None


@router.post("/{comment_id}/report", response_model=CommentReportResponse, status_code=status.HTTP_201_CREATED)
def report_comment(
    comment_id: int,
    report: CommentReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Yêu cầu đăng nhập
):
    """
    Report a comment
    
    **Authentication required**
    
    Reasons: spam, inappropriate, offensive, misleading, other
    """
    try:
        created_report = CommentService.report_comment(
            db=db,
            comment_id=comment_id,
            reporter_user_id=current_user["user_id"],
            reason=report.reason,
            description=report.description
        )
        
        return CommentReportResponse(
            id=created_report.id,
            comment_id=created_report.comment_id,
            reporter_user_id=created_report.reporter_user_id,
            reason=created_report.reason,
            description=created_report.description,
            status=created_report.status,
            created_at=created_report.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ADMIN ENDPOINTS ====================

@router.get("/admin/flagged", response_model=PaginatedCommentsResponse)
def get_flagged_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Get all flagged comments
    
    **Admin only**
    """
    comments_with_reports, total = CommentService.get_flagged_comments(
        db=db,
        page=page,
        page_size=page_size
    )
    
    items = []
    for item in comments_with_reports:
        comment = item['comment']
        items.append(
            CommentResponse(
                id=comment.id,
                user_id=comment.user_id,
                user_name=comment.user_name,
                user_email=comment.user_email,
                target_type=comment.target_type,
                target_id=comment.target_id,
                content=comment.content,
                rating=comment.rating,
                is_approved=comment.is_approved,
                is_flagged=comment.is_flagged,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                likes_count=0,
                user_has_liked=False
            )
        )
    
    total_pages = math.ceil(total / page_size)
    
    return PaginatedCommentsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/admin/reports", response_model=List[CommentReportResponse])
def get_pending_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Get pending reports
    
    **Admin only**
    """
    reports, total = CommentService.get_pending_reports(db, page, page_size)
    
    return [
        CommentReportResponse(
            id=r.id,
            comment_id=r.comment_id,
            reporter_user_id=r.reporter_user_id,
            reason=r.reason,
            description=r.description,
            status=r.status,
            created_at=r.created_at
        )
        for r in reports
    ]


@router.patch("/{comment_id}/moderate", response_model=CommentResponse)
def moderate_comment(
    comment_id: int,
    moderation: CommentModerationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Update comment moderation status
    
    **Admin only**
    
    Can approve/disapprove or flag/unflag comments
    """
    updated_comment = CommentService.update_comment_moderation(
        db=db,
        comment_id=comment_id,
        is_approved=moderation.is_approved,
        is_flagged=moderation.is_flagged
    )
    
    if not updated_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return CommentResponse(
        id=updated_comment.id,
        user_id=updated_comment.user_id,
        user_name=updated_comment.user_name,
        user_email=updated_comment.user_email,
        target_type=updated_comment.target_type,
        target_id=updated_comment.target_id,
        content=updated_comment.content,
        rating=updated_comment.rating,
        is_approved=updated_comment.is_approved,
        is_flagged=updated_comment.is_flagged,
        created_at=updated_comment.created_at,
        updated_at=updated_comment.updated_at,
        likes_count=0,
        user_has_liked=False
    )


@router.patch("/admin/reports/{report_id}/resolve")
def resolve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Resolve a report
    
    **Admin only**
    """
    resolved_report = CommentService.resolve_report(db, report_id)
    
    if not resolved_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report resolved successfully"}


@router.post("/admin/bulk-action")
def bulk_action(
    action: BulkCommentAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Perform bulk action on comments
    
    **Admin only**
    
    Actions: approve, flag, delete
    """
    if action.action == "delete":
        deleted_count = CommentService.bulk_delete_comments(db, action.comment_ids)
        return {"message": f"Deleted {deleted_count} comments"}
    
    elif action.action == "approve":
        for comment_id in action.comment_ids:
            CommentService.update_comment_moderation(db, comment_id, is_approved=True, is_flagged=False)
        return {"message": f"Approved {len(action.comment_ids)} comments"}
    
    elif action.action == "flag":
        for comment_id in action.comment_ids:
            CommentService.update_comment_moderation(db, comment_id, is_flagged=True)
        return {"message": f"Flagged {len(action.comment_ids)} comments"}


@router.get("/admin/statistics")
def get_admin_statistics(
    target_type: Optional[str] = Query(None, pattern="^(movie|theater)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)  # Chỉ Admin
):
    """
    Get aggregated statistics
    
    **Admin only**
    
    Overall statistics across all comments
    """
    stats = CommentService.get_aggregated_stats(db, target_type)
    return stats