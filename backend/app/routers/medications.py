import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, record_activity
from app.models import Profile, Medication, PendingChange, DoseLog
from app.schemas import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    CurrentUser
)
from app.services.dose_service import ensure_doses_generated_for_date

router = APIRouter(prefix="/api/medications", tags=["Medications"])

def med_to_response(med: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=med.id,
        profile_id=med.profile_id,
        name=med.name,
        dosage=med.dosage,
        frequency=med.frequency,
        schedule_times=med.get_times(),
        food_timing=med.food_timing,
        start_date=med.start_date,
        end_date=med.end_date,
        stock_count=med.stock_count,
        low_stock_threshold=med.low_stock_threshold,
        instructions=med.instructions or "",
        is_active=med.is_active,
        created_by_name=med.created_by_name,
        created_by_role=med.created_by_role,
        created_at=med.created_at
    )

@router.get("", response_model=List[MedicationResponse])
def list_medications(
    active_only: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Medication).filter(Medication.profile_id == current_user.profile_id)
    if active_only:
        query = query.filter(Medication.is_active == True)
    meds = query.order_by(Medication.name.asc()).all()
    return [med_to_response(m) for m in meds]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_medication(
    payload: MedicationCreate,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER", "FAMILY"])),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # If current user is ELDER, or CARETAKER with auto_approve enabled -> Apply directly
    is_direct = (
        current_user.role == "ELDER" or 
        (current_user.role == "CARETAKER" and profile.auto_approve_caretaker)
    )

    if is_direct:
        new_med = Medication(
            profile_id=profile.id,
            name=payload.name.strip(),
            dosage=payload.dosage.strip(),
            frequency=payload.frequency,
            schedule_times=json.dumps(payload.schedule_times),
            food_timing=payload.food_timing,
            start_date=payload.start_date,
            end_date=payload.end_date,
            stock_count=payload.stock_count,
            low_stock_threshold=payload.low_stock_threshold,
            instructions=payload.instructions or "",
            is_active=True,
            created_by_name=current_user.name,
            created_by_role=current_user.role
        )
        db.add(new_med)
        db.commit()
        db.refresh(new_med)

        # Generate today's dose if applicable
        ensure_doses_generated_for_date(db, profile.id, date.today())

        record_activity(
            db,
            profile.id,
            "MEDICATION_ADDED",
            f"Added medication '{new_med.name} ({new_med.dosage})'",
            current_user
        )

        return {
            "status": "APPROVED",
            "message": f"Medication '{new_med.name}' added successfully.",
            "data": med_to_response(new_med)
        }
    else:
        # Route to Pending Approval for Elder!
        pending = PendingChange(
            profile_id=profile.id,
            entity_type="MEDICATION",
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
            f"Proposed new medication '{payload.name}' (awaiting elder confirmation)",
            current_user
        )

        return {
            "status": "PENDING_APPROVAL",
            "message": f"Proposal submitted! Since you are a {current_user.role}, {profile.full_name} will review and confirm this change.",
            "pending_id": pending.id
        }


@router.put("/{med_id}")
def update_medication(
    med_id: int,
    payload: MedicationUpdate,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER", "FAMILY"])),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    med = db.query(Medication).filter(
        Medication.id == med_id,
        Medication.profile_id == current_user.profile_id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    is_direct = (
        current_user.role == "ELDER" or 
        (current_user.role == "CARETAKER" and profile.auto_approve_caretaker)
    )

    if is_direct:
        if payload.name is not None:
            med.name = payload.name.strip()
        if payload.dosage is not None:
            med.dosage = payload.dosage.strip()
        if payload.frequency is not None:
            med.frequency = payload.frequency
        if payload.schedule_times is not None:
            med.schedule_times = json.dumps(payload.schedule_times)
        if payload.food_timing is not None:
            med.food_timing = payload.food_timing
        if payload.start_date is not None:
            med.start_date = payload.start_date
        if payload.end_date is not None:
            med.end_date = payload.end_date
        if payload.stock_count is not None:
            med.stock_count = payload.stock_count
        if payload.low_stock_threshold is not None:
            med.low_stock_threshold = payload.low_stock_threshold
        if payload.instructions is not None:
            med.instructions = payload.instructions
        if payload.is_active is not None:
            med.is_active = payload.is_active

        db.commit()
        db.refresh(med)

        record_activity(
            db,
            profile.id,
            "MEDICATION_UPDATED",
            f"Updated medication '{med.name}'",
            current_user
        )

        return {
            "status": "APPROVED",
            "message": f"Medication '{med.name}' updated successfully.",
            "data": med_to_response(med)
        }
    else:
        pending = PendingChange(
            profile_id=profile.id,
            entity_type="MEDICATION",
            action_type="UPDATE",
            target_id=med.id,
            payload=json.dumps(payload.model_dump(exclude_unset=True, mode="json")),
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
            f"Proposed updates to '{med.name}' (awaiting elder approval)",
            current_user
        )

        return {
            "status": "PENDING_APPROVAL",
            "message": f"Update submitted for {profile.full_name}'s approval.",
            "pending_id": pending.id
        }


@router.delete("/{med_id}")
def delete_medication(
    med_id: int,
    current_user: CurrentUser = Depends(require_roles(["ELDER", "CARETAKER", "FAMILY"])),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    med = db.query(Medication).filter(
        Medication.id == med_id,
        Medication.profile_id == current_user.profile_id
    ).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    is_direct = (
        current_user.role == "ELDER" or 
        (current_user.role == "CARETAKER" and profile.auto_approve_caretaker)
    )

    if is_direct:
        med_name = med.name
        db.delete(med)
        db.commit()

        record_activity(
            db,
            profile.id,
            "MEDICATION_DELETED",
            f"Deleted medication '{med_name}'",
            current_user
        )
        return {"status": "DELETED", "message": f"Medication '{med_name}' removed."}
    else:
        pending = PendingChange(
            profile_id=profile.id,
            entity_type="MEDICATION",
            action_type="DELETE",
            target_id=med.id,
            payload=json.dumps({"name": med.name}),
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
            f"Proposed deletion of medication '{med.name}' (awaiting elder approval)",
            current_user
        )

        return {
            "status": "PENDING_APPROVAL",
            "message": f"Deletion proposal submitted for elder review."
        }
