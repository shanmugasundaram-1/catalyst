import pytest
from app.services.gemini_service import (
    parse_natural_language_medication,
    check_drug_interaction,
    generate_weekly_family_summary,
    scan_prescription_image
)
from app.services.email_service import (
    send_upcoming_dose_email,
    send_escalation_missed_dose,
    send_sos_alert,
    sent_email_history
)

def test_natural_language_medication_parsing():
    text = "Metformin 500mg morning and night after food for 30 days"
    result = parse_natural_language_medication(text)
    assert result is not None
    assert "Metformin" in result["name"] or "metformin" in result["name"].lower()
    assert "500" in result["dosage"]
    assert result["food_timing"] == "AFTER_FOOD"
    assert len(result["schedule_times"]) >= 1

def test_drug_interaction_checker():
    # Test safe medicine
    safe_result = check_drug_interaction("Paracetamol 500mg", ["Metformin 500mg", "Telmisartan 40mg"])
    assert "disclaimer" in safe_result
    assert "overall_status" in safe_result

    # Test caution medicine (Aspirin with blood thinner)
    caution_result = check_drug_interaction("Aspirin 150mg", ["Warfarin blood thinner", "Metformin"])
    assert "disclaimer" in caution_result
    assert len(caution_result["warnings"]) >= 1 or caution_result["has_warning"] is True

def test_weekly_summary_multilingual():
    summary = generate_weekly_family_summary(
        elder_name="Broly",
        adherence_pct=92.5,
        taken_count=26,
        missed_count=2,
        upcoming_appointments=["Dr. Ramanathan (Cardiologist) on Tue 10:30 AM"]
    )
    assert "friendly_summary_en" in summary
    assert "friendly_summary_ta" in summary
    assert len(summary["friendly_summary_en"]) > 20
    assert len(summary["friendly_summary_ta"]) > 20
    assert len(summary["doctor_talking_points"]) >= 1

def test_prescription_scanner_structure():
    # Test image scanner fallback structure with sample bytes
    dummy_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    result = scan_prescription_image(dummy_bytes, mime_type="image/gif")
    assert "medications" in result
    assert len(result["medications"]) >= 1
    med = result["medications"][0]
    assert "name" in med
    assert "dosage" in med
    assert "schedule_times" in med

def test_email_notifications_and_audit():
    initial_count = len(sent_email_history)
    
    # 1. Upcoming dose email
    send_upcoming_dose_email(
        elder_email="elder@test.org",
        elder_name="Broly",
        med_name="Metformin",
        dosage="500 mg",
        scheduled_time_str="08:30 AM",
        food_timing="AFTER_FOOD"
    )

    # 2. Missed dose level 1 (Elder)
    send_escalation_missed_dose(
        level=1,
        recipients=["elder@test.org"],
        elder_name="Broly",
        med_name="Metformin",
        dosage="500 mg",
        scheduled_time_str="08:30 AM"
    )

    # 3. Missed dose level 2 (Caretaker)
    send_escalation_missed_dose(
        level=2,
        recipients=["caretaker@test.org"],
        elder_name="Broly",
        med_name="Metformin",
        dosage="500 mg",
        scheduled_time_str="08:30 AM"
    )

    # 4. Missed dose level 3 (Family)
    send_escalation_missed_dose(
        level=3,
        recipients=["family@test.org"],
        elder_name="Broly",
        med_name="Metformin",
        dosage="500 mg",
        scheduled_time_str="08:30 AM"
    )

    # 5. SOS Alert
    send_sos_alert(
        recipients=["caretaker@test.org", "family@test.org"],
        elder_name="Broly",
        timestamp_str="Sunday 10:30 AM",
        emergency_phone="+91 98401 23456",
        notes="Bedside emergency"
    )

    # Verify history audit
    assert len(sent_email_history) == initial_count + 5
    assert sent_email_history[0]["subject"].startswith("URGENT: SOS Alert")
