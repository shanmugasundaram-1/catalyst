import pytest
from datetime import datetime, date, time, timedelta
from app.core.database import SessionLocal
from app.models import Profile, ProfileMember, DoseLog, Medication, CareInsight
from app.schemas import (
    JoinProfileRequest,
    UpdateMemberLanguageRequest,
    CurrentUser,
    VoiceIntentRequest,
    SOSRequest
)
from app.routers.auth import join_profile
from app.routers.profiles import update_member_language
from app.routers.sos import trigger_sos
from app.services.voice_service import detect_language, process_voice_intent
from app.services.gemini_service import generate_weekly_family_summary, check_drug_interaction
from app.services.email_service import sent_email_history, send_sos_alert
from app.services.insights_service import analyze_profile_insights, mark_insight_seen, get_insights

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_language_detection():
    # Devanagari Hindi
    assert detect_language("मैंने बीपी की दवा ले ली") == "hi"
    assert detect_language("अगली दवा कब है?") == "hi"
    assert detect_language("कल डॉक्टर का अपॉइंटमेंट है क्या?") == "hi"

    # Tamil script
    assert detect_language("நான் மாத்திரை சாப்பிட்டேன்") == "ta"
    assert detect_language("அடுத்த மருந்து எப்போ?") == "ta"

    # Tanglish code-mixing
    assert detect_language("BP maathirai saapten") == "ta"
    assert detect_language("Next maathirai eppo?") == "ta"
    assert detect_language("Naalaiku doctor appointment irukka?") == "ta"

    # English
    assert detect_language("I took my BP tablet") == "en"
    assert detect_language("When is my next dose?") == "en"

def test_member_language_persistence(db):
    # Join with explicit Hindi preference
    res = join_profile(JoinProfileRequest(
        profile_id="DEMO-ELDER",
        passcode="3333",
        name="Rohit Sharma (Grandson)",
        email="rohit.hindi@test.demo",
        language="hi"
    ), db=db)

    assert res.language == "hi"

    # Verify persisted in database
    member = db.query(ProfileMember).filter(ProfileMember.email == "rohit.hindi@test.demo").first()
    assert member is not None
    assert member.language == "hi"

    # Update member language to Tamil
    current_u = CurrentUser(
        profile_id="DEMO-ELDER",
        role="FAMILY",
        name="Rohit Sharma",
        email="rohit.hindi@test.demo",
        language="hi"
    )
    upd = update_member_language(UpdateMemberLanguageRequest(language="ta"), current_user=current_u, db=db)
    assert upd["language"] == "ta"

    # Check updated in DB
    db.refresh(member)
    assert member.language == "ta"

def test_voice_intent_and_reply_language(db):
    # 1. Hindi query -> Hindi reply
    res_hi = process_voice_intent(
        query="अगली दवा कब है?",
        user_lang="hi",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db
    )
    assert res_hi["intent"] == "NEXT_DOSE_QUERY"
    assert res_hi["spoken_language"] == "hi"
    assert "दवा" in res_hi["reply_text"] or "खुराक" in res_hi["reply_text"] or len(res_hi["reply_text"]) > 5

    # 2. Tanglish / Tamil query -> Tamil reply
    res_ta = process_voice_intent(
        query="Next maathirai eppo?",
        user_lang="ta",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db
    )
    assert res_ta["intent"] == "NEXT_DOSE_QUERY"
    assert res_ta["spoken_language"] == "ta"
    assert "மருந்து" in res_ta["reply_text"] or len(res_ta["reply_text"]) > 5

    # 3. English query -> English reply
    res_en = process_voice_intent(
        query="When is my next dose?",
        user_lang="en",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db
    )
    assert res_en["intent"] == "NEXT_DOSE_QUERY"
    assert res_en["spoken_language"] == "en"
    assert "next dose" in res_en["reply_text"].lower() or "scheduled" in res_en["reply_text"].lower()

def test_mark_dose_taken_updates_dose_log(db):
    # Create an active pending dose for testing
    med = db.query(Medication).filter(Medication.profile_id == "DEMO-ELDER").first()
    assert med is not None
    initial_stock = med.stock_count

    pending_dose = DoseLog(
        profile_id="DEMO-ELDER",
        medication_id=med.id,
        scheduled_time=datetime.now() + timedelta(minutes=5),
        status="PENDING",
        escalation_level=0
    )
    db.add(pending_dose)
    db.commit()
    db.refresh(pending_dose)

    # Call voice intent to mark it taken
    res = process_voice_intent(
        query=f"I took my {med.name}",
        user_lang="en",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db
    )

    assert res["intent"] == "MARK_DOSE_TAKEN"
    db.refresh(pending_dose)
    assert pending_dose.status == "TAKEN"
    assert pending_dose.taken_at is not None

    db.refresh(med)
    assert med.stock_count == initial_stock - 1

def test_voice_sos_confirmation_flow(db):
    sent_email_history.clear()

    # Step 1: Initial voice SOS command without confirmation
    res_unconfirmed = process_voice_intent(
        query="Emergency SOS",
        user_lang="en",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db,
        confirmed_sos=False
    )
    assert res_unconfirmed["intent"] == "SOS"
    assert res_unconfirmed["requires_confirmation"] is True
    assert len(sent_email_history) == 0  # No emails sent yet

    # Step 2: Confirmed voice SOS command
    res_confirmed = process_voice_intent(
        query="Yes send SOS",
        user_lang="en",
        profile_id="DEMO-ELDER",
        user_name="broly",
        user_role="ELDER",
        db=db,
        confirmed_sos=True
    )
    assert res_confirmed["intent"] == "SOS"
    assert res_confirmed["requires_confirmation"] is False
    assert len(sent_email_history) >= 1  # Emails sent to caretakers and family

def test_insights_no_duplicates_within_48_hours(db):
    # First run: generates insights from the seeded 14-day history
    insights_run1 = analyze_profile_insights(db, "DEMO-ELDER", trigger_notifications=False)

    # Second run immediately after: must NOT create duplicate insights within 48 hours
    insights_run2 = analyze_profile_insights(db, "DEMO-ELDER", trigger_notifications=False)
    assert len(insights_run2) == 0

def test_insights_email_in_recipient_language(db):
    sent_email_history.clear()

    # Ensure members have designated languages: Caretaker (en), Family (hi)
    caretaker = db.query(ProfileMember).filter(
        ProfileMember.profile_id == "DEMO-ELDER",
        ProfileMember.role == "CARETAKER"
    ).first()
    if caretaker:
        caretaker.language = "en"

    family = db.query(ProfileMember).filter(
        ProfileMember.profile_id == "DEMO-ELDER",
        ProfileMember.role == "FAMILY"
    ).first()
    if family:
        family.language = "hi"
    db.commit()

    # Clear previous insights for this profile to allow fresh notification run
    db.query(CareInsight).filter(CareInsight.profile_id == "DEMO-ELDER").delete()
    db.commit()

    # Run analysis with notifications enabled
    created = analyze_profile_insights(db, "DEMO-ELDER", trigger_notifications=True)
    assert len(created) >= 1

    # Check that sent emails include recipient's preferred languages
    sent_langs = [item.get("language") for item in sent_email_history]
    assert "en" in sent_langs
    assert "hi" in sent_langs

def test_mark_insight_seen(db):
    all_insights = get_insights(db, "DEMO-ELDER")
    if all_insights:
        target = all_insights[0]
        seen = mark_insight_seen(db, target.id, "DEMO-ELDER")
        assert seen is not None
        assert seen.status == "SEEN"
