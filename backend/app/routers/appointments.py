import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, record_activity
from app.models import Appointment, Profile, PendingChange
from app.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    CurrentUser
)

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

def appt_to_response(a: Appointment) -> AppointmentResponse:
    return AppointmentResponse(
        id=a.id,
        profile_id=a.profile_id,
        doctor_name=a.doctor_name,
        specialty=a.specialty,
        appointment_time=a.appointment_time,
        location=a.location,
        notes=a.notes or "",
        is_completed=a.is_completed,
        created_by_name=a.created_by_name or "Care Circle",
        created_at=a.created_at
    )

@router.get("", response_model=List[AppointmentResponse])
def list_appointments(
    upcoming_only: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Appointment).filter(Appointment.profile_id == current_user.profile_id)
    if upcoming_only:
        query = query.filter(Appointment.appointment_time >= datetime.now(), Appointment.is_completed == False)
    appts = query.order_by(Appointment.appointment_time.asc()).all()
    return [appt_to_response(a) for a in appts]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER", "FAMILY"])),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    is_direct = (
        current_user.role == "ELDER" or 
        (current_user.role == "CARETAKER" and profile.auto_approve_caretaker)
    )

    if is_direct:
        new_appt = Appointment(
            profile_id=profile.id,
            doctor_name=payload.doctor_name.strip(),
            specialty=payload.specialty.strip(),
            appointment_time=payload.appointment_time,
            location=payload.location.strip(),
            notes=payload.notes or "",
            created_by_name=current_user.name
        )
        db.add(new_appt)
        db.commit()
        db.refresh(new_appt)

        record_activity(
            db,
            profile.id,
            "APPOINTMENT_SCHEDULED",
            f"Scheduled appointment with Dr. {new_appt.doctor_name} for {new_appt.appointment_time.strftime('%b %d, %I:%M %p')}",
            current_user
        )

        return {
            "status": "APPROVED",
            "message": f"Appointment with Dr. {new_appt.doctor_name} confirmed.",
            "data": appt_to_response(new_appt)
        }
    else:
        pending = PendingChange(
            profile_id=profile.id,
            entity_type="APPOINTMENT",
            action_type="CREATE",
            target_id=None,
            payload=json.dumps(payload.model_dump(mode="json")),
            status="PENDING",
            proposed_by_name=current_user.name,
            proposed_by_role=current_user.role
        )
        db.add(pending)
        db.commit()

        record_activity(
            db,
            profile.id,
            "CHANGE_PROPOSED",
            f"Proposed doctor visit with Dr. {payload.doctor_name} (awaiting elder approval)",
            current_user
        )

        return {
            "status": "PENDING_APPROVAL",
            "message": f"Appointment proposal submitted for {profile.full_name}'s review.",
            "pending_id": pending.id
        }


@router.patch("/{appt_id}/status")
def toggle_appointment_complete(
    appt_id: int,
    completed: bool = True,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER"])),
    db: Session = Depends(get_db)
):
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.profile_id == current_user.profile_id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.is_completed = completed
    db.commit()

    record_activity(
        db,
        current_user.profile_id,
        "APPOINTMENT_UPDATED",
        f"Marked appointment with Dr. {appt.doctor_name} as {'Completed' if completed else 'Pending'}",
        current_user
    )

    return appt_to_response(appt)


@router.delete("/{appt_id}")
def delete_appointment(
    appt_id: int,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER"])),
    db: Session = Depends(get_db)
):
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.profile_id == current_user.profile_id
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    doctor = appt.doctor_name
    db.delete(appt)
    db.commit()

    record_activity(
        db,
        current_user.profile_id,
        "APPOINTMENT_CANCELLED",
        f"Cancelled appointment with Dr. {doctor}",
        current_user
    )

    return {"status": "DELETED", "message": f"Appointment with Dr. {doctor} removed"}
