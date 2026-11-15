from datetime import datetime, timezone, timedelta, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, record_activity
from app.models import DoseLog, Medication, Profile
from app.schemas import (
    TodayOverviewResponse,
    DoseLogResponse,
    DoseActionRequest,
    CurrentUser
)
from app.services.dose_service import (
    get_today_doses,
    get_next_dose,
    calculate_adherence_stats,
    ensure_doses_generated_for_date
)

router = APIRouter(prefix="/api/doses", tags=["Dose Tracking"])

def dose_to_response(d: DoseLog) -> DoseLogResponse:
    med = d.medication
    return DoseLogResponse(
        id=d.id,
        profile_id=d.profile_id,
        medication_id=d.medication_id,
        medication_name=med.name if med else "Unknown Medication",
        dosage=med.dosage if med else "",
        food_timing=med.food_timing if med else "AFTER_FOOD",
        scheduled_time=d.scheduled_time,
        status=d.status,
        taken_at=d.taken_at,
        taken_by_name=d.taken_by_name,
        notes=d.notes or "",
        escalation_level=d.escalation_level
    )

@router.get("/today", response_model=TodayOverviewResponse)
def get_today_overview(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile_id = current_user.profile_id
    today_doses = get_today_doses(db, profile_id)
    next_d = get_next_dose(db, profile_id)
    stats = calculate_adherence_stats(db, profile_id, days=7)

    return TodayOverviewResponse(
        next_dose=dose_to_response(next_d) if next_d else None,
        today_doses=[dose_to_response(d) for d in today_doses],
        adherence_percentage=stats["adherence_percentage"],
        streak_days=stats["streak_days"],
        total_scheduled=len(today_doses),
        total_taken=sum(1 for d in today_doses if d.status == "TAKEN"),
        total_missed=sum(1 for d in today_doses if d.status == "MISSED")
    )


@router.post("/{dose_id}/action", response_model=DoseLogResponse)
def record_dose_action(
    dose_id: int,
    payload: DoseActionRequest,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER"])),
    db: Session = Depends(get_db)
):
    dose = db.query(DoseLog).filter(
        DoseLog.id == dose_id,
        DoseLog.profile_id == current_user.profile_id
    ).first()

    if not dose:
        raise HTTPException(status_code=404, detail="Dose log record not found")

    new_status = payload.status.upper().strip()
    if new_status not in ["TAKEN", "SKIPPED", "MISSED", "PENDING"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be TAKEN, SKIPPED, or MISSED")

    old_status = dose.status
    dose.status = new_status
    dose.notes = payload.notes or ""

    if new_status == "TAKEN":
        dose.taken_at = datetime.now()
        dose.taken_by_name = current_user.name
        # Decrement stock count if wasn't already taken
        if old_status != "TAKEN" and dose.medication:
            if dose.medication.stock_count > 0:
                dose.medication.stock_count -= 1
            if dose.medication.stock_count <= dose.medication.low_stock_threshold:
                record_activity(
                    db,
                    current_user.profile_id,
                    "LOW_STOCK_WARNING",
                    f"Low stock for {dose.medication.name}: {dose.medication.stock_count} units remaining",
                    current_user
                )
    else:
        if new_status == "PENDING":
            dose.taken_at = None
            dose.taken_by_name = None

    db.commit()
    db.refresh(dose)

    action_label = "DOSE_TAKEN" if new_status == "TAKEN" else f"DOSE_{new_status}"
    med_name = dose.medication.name if dose.medication else "Medication"
    record_activity(
        db,
        current_user.profile_id,
        action_label,
        f"{current_user.name} ({current_user.role}) marked {med_name} as {new_status}",
        current_user
    )

    return dose_to_response(dose)


@router.get("/history")
def get_dose_history(
    days: int = 7,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns daily stats breakdown for the past N days for charting in Recharts.
    """
    profile_id = current_user.profile_id
    today = date.today()
    chart_data = []

    for i in range(days - 1, -1, -1):
        target_d = today - timedelta(days=i)
        start_dt = datetime.combine(target_d, time.min)
        end_dt = datetime.combine(target_d, time.max)

        day_logs = db.query(DoseLog).filter(
            DoseLog.profile_id == profile_id,
            DoseLog.scheduled_time >= start_dt,
            DoseLog.scheduled_time <= end_dt
        ).all()

        taken = sum(1 for d in day_logs if d.status == "TAKEN")
        missed = sum(1 for d in day_logs if d.status == "MISSED")
        skipped = sum(1 for d in day_logs if d.status == "SKIPPED")
        pending = sum(1 for d in day_logs if d.status == "PENDING")
        total = len(day_logs)

        chart_data.append({
            "date": target_d.strftime("%b %d"),
            "full_date": target_d.isoformat(),
            "taken": taken,
            "missed": missed,
            "skipped": skipped,
            "pending": pending,
            "total": total,
            "adherence": round((taken / (taken + missed + skipped) * 100), 1) if (taken + missed + skipped) > 0 else 100.0
        })

    stats = calculate_adherence_stats(db, profile_id, days=days)
    return {
        "history": chart_data,
        "summary": stats
    }
