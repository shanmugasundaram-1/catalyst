from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, CurrentUser, record_activity
from app.schemas import CareInsightResponse
from app.services.insights_service import get_insights, mark_insight_seen, analyze_profile_insights

router = APIRouter(prefix="/api/insights", tags=["AI Early Warning & Care Insights"])

@router.get("", response_model=List[CareInsightResponse])
def fetch_insights(
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns latest care insights for the current elder profile, newest first.
    Color-coded by severity: urgent (red), warning (amber), info (blue).
    """
    return get_insights(db, current_user.profile_id, limit=limit)


@router.post("/analyze", response_model=List[CareInsightResponse])
def trigger_immediate_analysis(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers on-demand 14-day analysis of dose logs and stock to generate immediate insights for demo.
    """
    insights = analyze_profile_insights(db, current_user.profile_id, trigger_notifications=True)
    return insights


@router.post("/{insight_id}/seen", response_model=CareInsightResponse)
def acknowledge_insight(
    insight_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks an insight as SEEN.
    """
    insight = mark_insight_seen(db, insight_id, current_user.profile_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    record_activity(
        db,
        current_user.profile_id,
        "INSIGHT_ACKNOWLEDGED",
        f"Care insight #{insight_id} ({insight.title_en}) marked as seen by {current_user.name}",
        current_user
    )
    return insight
