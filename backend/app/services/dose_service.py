from datetime import datetime, date, time, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Medication, DoseLog, Profile

def ensure_doses_generated_for_date(db: Session, profile_id: str, target_date: date):
    """
    Ensures that for all active medications in the profile, DoseLog rows exist for target_date.
    """
    medications = db.query(Medication).filter(
        Medication.profile_id == profile_id,
        Medication.is_active == True,
        Medication.start_date <= target_date
    ).all()

    for med in medications:
        if med.end_date and med.end_date < target_date:
            continue
        
        times = med.get_times()
        for t_str in times:
            try:
                parts = t_str.strip().split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                scheduled_dt = datetime.combine(target_date, time(hour, minute))
            except Exception:
                continue

            # Check if dose log already exists for this medication and scheduled time
            existing = db.query(DoseLog).filter(
                DoseLog.medication_id == med.id,
                DoseLog.scheduled_time == scheduled_dt
            ).first()

            if not existing:
                new_log = DoseLog(
                    profile_id=profile_id,
                    medication_id=med.id,
                    scheduled_time=scheduled_dt,
                    status="PENDING",
                    escalation_level=0
                )
                db.add(new_log)
    db.commit()


def get_today_doses(db: Session, profile_id: str) -> List[DoseLog]:
    today = date.today()
    ensure_doses_generated_for_date(db, profile_id, today)

    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    doses = db.query(DoseLog).filter(
        DoseLog.profile_id == profile_id,
        DoseLog.scheduled_time >= start_of_day,
        DoseLog.scheduled_time <= end_of_day
    ).order_by(DoseLog.scheduled_time.asc()).all()

    return doses


def get_next_dose(db: Session, profile_id: str) -> Optional[DoseLog]:
    now = datetime.now()
    doses = get_today_doses(db, profile_id)
    # Find first pending dose for today
    pending = [d for d in doses if d.status == "PENDING"]
    if pending:
        # Return the earliest pending dose
        return pending[0]
    
    # If all today's are taken or missed, find upcoming pending in future
    future_dose = db.query(DoseLog).filter(
        DoseLog.profile_id == profile_id,
        DoseLog.status == "PENDING",
        DoseLog.scheduled_time >= now
    ).order_by(DoseLog.scheduled_time.asc()).first()

    return future_dose


def calculate_adherence_stats(db: Session, profile_id: str, days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    logs = db.query(DoseLog).filter(
        DoseLog.profile_id == profile_id,
        DoseLog.scheduled_time >= cutoff_date
    ).all()

    total = len(logs)
    taken = sum(1 for d in logs if d.status == "TAKEN")
    missed = sum(1 for d in logs if d.status == "MISSED")
    skipped = sum(1 for d in logs if d.status == "SKIPPED")
    pending = sum(1 for d in logs if d.status == "PENDING")

    # Percentage based on resolved doses (taken + missed + skipped)
    resolved = taken + missed + skipped
    percentage = round((taken / resolved * 100), 1) if resolved > 0 else 100.0

    # Calculate streak (consecutive days with 100% taken or no missed)
    streak = 0
    today = date.today()
    for d_offset in range(1, 31):
        check_day = today - timedelta(days=d_offset)
        start_dt = datetime.combine(check_day, time.min)
        end_dt = datetime.combine(check_day, time.max)
        day_logs = db.query(DoseLog).filter(
            DoseLog.profile_id == profile_id,
            DoseLog.scheduled_time >= start_dt,
            DoseLog.scheduled_time <= end_dt
        ).all()

        if not day_logs:
            continue
        day_missed = any(l.status == "MISSED" for l in day_logs)
        day_taken = any(l.status == "TAKEN" for l in day_logs)
        if day_taken and not day_missed:
            streak += 1
        else:
            break

    return {
        "adherence_percentage": percentage,
        "streak_days": streak,
        "total_scheduled": total,
        "total_taken": taken,
        "total_missed": missed,
        "total_skipped": skipped,
        "total_pending": pending
    }
