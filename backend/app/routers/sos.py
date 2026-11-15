from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, CurrentUser, record_activity
from app.models import Profile, ProfileMember
from app.schemas import SOSRequest, SOSResponse
from app.services.email_service import send_sos_alert

router = APIRouter(prefix="/api/sos", tags=["Emergency SOS"])

@router.post("", response_model=SOSResponse)
def trigger_sos(
    payload: SOSRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Emergency SOS: Immediately dispatches urgent alerts to Caretaker and all Family members.
    """
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Fetch Caretakers and Family
    members = db.query(ProfileMember).filter(
        ProfileMember.profile_id == profile.id,
        ProfileMember.role.in_(["CARETAKER", "FAMILY"])
    ).all()

    recipient_emails = [m.email for m in members if m.email]
    now = datetime.now()
    now_str = now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

    # Send high-priority alert email grouped by recipient language
    lang_groups = {}
    for m in members:
        if m.email:
            l = m.language or "en"
            lang_groups.setdefault(l, []).append(m.email)

    for l, emails in lang_groups.items():
        send_sos_alert(
            recipients=emails,
            elder_name=profile.full_name,
            timestamp_str=now_str,
            emergency_phone=profile.emergency_phone,
            notes=profile.emergency_notes,
            lang=l
        )

    record_activity(
        db,
        profile.id,
        "EMERGENCY_SOS_TRIGGERED",
        f"🚨 SOS triggered by {current_user.name}! Emergency notifications sent to {len(recipient_emails)} contacts.",
        current_user
    )

    return SOSResponse(
        status="EMERGENCY_DISPATCHED",
        message=f"SOS alert broadcast to {len(recipient_emails)} care circle members.",
        timestamp=now,
        recipients_notified=recipient_emails
    )
