import json
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, record_activity
from app.models import PendingChange, Medication, Appointment, Profile
from app.schemas import PendingChangeResponse, PendingChangeReview, CurrentUser
from app.services.dose_service import ensure_doses_generated_for_date

router = APIRouter(prefix="/api/approvals", tags=["Elder Approval Workflow"])

def pending_to_response(p: PendingChange) -> PendingChangeResponse:
    try:
        payload_dict = json.loads(p.payload)
    except Exception:
        payload_dict = {"raw": p.payload}

    return PendingChangeResponse(
        id=p.id,
        profile_id=p.profile_id,
        entity_type=p.entity_type,
        action_type=p.action_type,
        target_id=p.target_id,
        payload=payload_dict,
        status=p.status,
        proposed_by_name=p.proposed_by_name,
        proposed_by_role=p.proposed_by_role,
        proposed_at=p.proposed_at,
        reviewed_by=p.reviewed_by,
        reviewed_at=p.reviewed_at,
        rejection_reason=p.rejection_reason
    )

@router.get("", response_model=List[PendingChangeResponse])
def list_pending_changes(
    status_filter: Optional[str] = "PENDING",
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PendingChange).filter(PendingChange.profile_id == current_user.profile_id)
    if status_filter:
        query = query.filter(PendingChange.status == status_filter.upper())
    changes = query.order_by(PendingChange.proposed_at.desc()).all()
    return [pending_to_response(c) for c in changes]


@router.post("/{change_id}/review", response_model=PendingChangeResponse)
def review_pending_change(
    change_id: int,
    review: PendingChangeReview,
    current_user: CurrentUser = Depends(require_roles(["ELDER"])),
    db: Session = Depends(get_db)
):
    """
    ELDER-ONLY: Approve or reject a pending change submitted by Caretaker or Family.
    """
    pending = db.query(PendingChange).filter(
        PendingChange.id == change_id,
        PendingChange.profile_id == current_user.profile_id
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending change not found")

    if pending.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"This request has already been {pending.status.lower()}")

    action = review.action.upper().strip()
    if action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    now = datetime.now()
    pending.reviewed_by = current_user.name
    pending.reviewed_at = now

    if action == "REJECT":
        pending.status = "REJECTED"
        pending.rejection_reason = review.rejection_reason or "Declined by Elder"
        db.commit()

        record_activity(
            db,
            current_user.profile_id,
            "CHANGE_REJECTED",
            f"Elder declined {pending.entity_type} {pending.action_type} proposed by {pending.proposed_by_name}",
            current_user
        )
        return pending_to_response(pending)

    # If APPROVED -> Apply change to real tables!
    pending.status = "APPROVED"
    payload = json.loads(pending.payload)

    if pending.entity_type == "MEDICATION":
        if pending.action_type == "CREATE":
            start_d = date.fromisoformat(payload["start_date"]) if "start_date" in payload else date.today()
            end_d = date.fromisoformat(payload["end_date"]) if payload.get("end_date") else None
            
            times = payload.get("schedule_times", ["09:00"])
            new_med = Medication(
                profile_id=current_user.profile_id,
                name=payload["name"],
                dosage=payload.get("dosage", "1 dose"),
                frequency=payload.get("frequency", "DAILY"),
                schedule_times=json.dumps(times),
                food_timing=payload.get("food_timing", "AFTER_FOOD"),
                start_date=start_d,
                end_date=end_d,
                stock_count=payload.get("stock_count", 30),
                low_stock_threshold=payload.get("low_stock_threshold", 5),
                instructions=payload.get("instructions", ""),
                is_active=True,
                created_by_name=pending.proposed_by_name,
                created_by_role=pending.proposed_by_role
            )
            db.add(new_med)
            db.commit()
            db.refresh(new_med)
            ensure_doses_generated_for_date(db, current_user.profile_id, date.today())

        elif pending.action_type == "UPDATE" and pending.target_id:
            med = db.query(Medication).filter(
                Medication.id == pending.target_id,
                Medication.profile_id == current_user.profile_id
            ).first()
            if med:
                for k, v in payload.items():
                    if k == "schedule_times":
                        med.schedule_times = json.dumps(v)
                    elif k in ["start_date", "end_date"] and v:
                        setattr(med, k, date.fromisoformat(v))
                    elif hasattr(med, k):
                        setattr(med, k, v)
                db.commit()

        elif pending.action_type == "DELETE" and pending.target_id:
            med = db.query(Medication).filter(
                Medication.id == pending.target_id,
                Medication.profile_id == current_user.profile_id
            ).first()
            if med:
                db.delete(med)
                db.commit()

    elif pending.entity_type == "APPOINTMENT":
        if pending.action_type == "CREATE":
            appt_time = datetime.fromisoformat(payload["appointment_time"].replace("Z", "+00:00"))
            new_appt = Appointment(
                profile_id=current_user.profile_id,
                doctor_name=payload["doctor_name"],
                specialty=payload.get("specialty", "General"),
                appointment_time=appt_time,
                location=payload.get("location", "Clinic"),
                notes=payload.get("notes", ""),
                created_by_name=pending.proposed_by_name
            )
            db.add(new_appt)
            db.commit()

    db.commit()
    db.refresh(pending)

    record_activity(
        db,
        current_user.profile_id,
        "CHANGE_APPROVED",
        f"Elder approved {pending.entity_type} {pending.action_type} proposed by {pending.proposed_by_name}",
        current_user
    )

    return pending_to_response(pending)
