import pytest
from datetime import date
from fastapi import HTTPException
from app.core.database import SessionLocal
from app.schemas import (
    JoinProfileRequest,
    CreateProfileRequest,
    CurrentUser,
    ProfileSettingsUpdate,
    MedicationCreate,
    PendingChangeReview,
    DoseActionRequest,
    SOSRequest
)
from app.routers.auth import join_profile, register_profile
from app.routers.profiles import get_current_profile, update_profile_settings
from app.routers.medications import create_medication, list_medications
from app.routers.approvals import list_pending_changes, review_pending_change
from app.routers.doses import get_today_overview, record_dose_action
from app.routers.sos import trigger_sos

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_join_roles(db):
    # Test Elder Passcode
    elder_res = join_profile(JoinProfileRequest(
        profile_id="DEMO-ELDER",
        passcode="1111",
        name="Broly",
        email="broly@test.demo"
    ), db=db)
    assert elder_res.role == "ELDER"
    assert elder_res.profile_id == "DEMO-ELDER"
    assert len(elder_res.access_token) > 20

    # Test Caretaker Passcode
    caretaker_res = join_profile(JoinProfileRequest(
        profile_id="DEMO-ELDER",
        passcode="2222",
        name="Priya Nurse",
        email="priya@test.demo"
    ), db=db)
    assert caretaker_res.role == "CARETAKER"

    # Test Family Passcode
    family_res = join_profile(JoinProfileRequest(
        profile_id="DEMO-ELDER",
        passcode="3333",
        name="Karthik Son",
        email="karthik@test.demo"
    ), db=db)
    assert family_res.role == "FAMILY"

    # Test Invalid Passcode
    with pytest.raises(HTTPException) as exc_info:
        join_profile(JoinProfileRequest(
            profile_id="DEMO-ELDER",
            passcode="0000_wrong",
            name="Intruder",
            email="intruder@bad.demo"
        ), db=db)
    assert exc_info.value.status_code == 401

def test_elder_vs_caretaker_approval_workflow(db):
    caretaker_user = CurrentUser(
        profile_id="DEMO-ELDER",
        role="CARETAKER",
        name="Priya Caretaker",
        email="priya@test.demo"
    )

    # 1. Caretaker submits new medication -> goes to PENDING_APPROVAL
    med_payload = MedicationCreate(
        name="Test Calcium Supplement",
        dosage="500 mg",
        frequency="DAILY",
        schedule_times=["14:00"],
        food_timing="AFTER_FOOD",
        start_date=date.today(),
        stock_count=30,
        low_stock_threshold=5,
        instructions="Take with water"
    )
    result = create_medication(payload=med_payload, current_user=caretaker_user, db=db)
    assert result["status"] == "PENDING_APPROVAL"
    pending_id = result["pending_id"]

    # 2. Elder reviews and approves
    elder_user = CurrentUser(
        profile_id="DEMO-ELDER",
        role="ELDER",
        name="Broly",
        email="broly@test.demo"
    )
    approval_result = review_pending_change(
        change_id=pending_id,
        review=PendingChangeReview(action="APPROVE"),
        current_user=elder_user,
        db=db
    )
    assert approval_result.status == "APPROVED"
    assert approval_result.reviewed_by == "Broly"

def test_dose_tracking_and_stock(db):
    elder_user = CurrentUser(
        profile_id="DEMO-ELDER",
        role="ELDER",
        name="Broly",
        email="broly@test.demo"
    )

    overview = get_today_overview(current_user=elder_user, db=db)
    assert len(overview.today_doses) > 0
    assert overview.adherence_percentage >= 0

    first_dose = overview.today_doses[0]
    action_res = record_dose_action(
        dose_id=first_dose.id,
        payload=DoseActionRequest(status="TAKEN", notes="Dose verified"),
        current_user=elder_user,
        db=db
    )
    assert action_res.status == "TAKEN"
    assert action_res.taken_by_name == "Broly"

def test_emergency_sos(db):
    elder_user = CurrentUser(
        profile_id="DEMO-ELDER",
        role="ELDER",
        name="Broly",
        email="broly@test.demo"
    )
    sos_res = trigger_sos(
        payload=SOSRequest(location_note="Bedside"),
        current_user=elder_user,
        db=db
    )
    assert sos_res.status == "EMERGENCY_DISPATCHED"
    assert len(sos_res.recipients_notified) >= 1
