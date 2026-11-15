from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, CurrentUser, record_activity
from app.models import Medication, Appointment, Profile, ProfileMember
from app.schemas import (
    PrescriptionScanResponse,
    NaturalLanguageMedRequest,
    DrugInteractionRequest,
    DrugInteractionResponse,
    WeeklySummaryResponse
)
from app.services.gemini_service import (
    scan_prescription_image,
    parse_natural_language_medication,
    check_drug_interaction,
    generate_weekly_family_summary
)
from app.services.dose_service import calculate_adherence_stats
from app.services.email_service import (
    send_weekly_summary_email,
    sent_email_history
)
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/api/ai", tags=["Google Gemini AI Features"])

@router.post("/scan-prescription", response_model=PrescriptionScanResponse)
async def scan_prescription(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Multimodal Gemini Vision Scanner:
    Extracts medicines, dosage, and timings from a prescription photo.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG, WEBP)")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit")

    result = scan_prescription_image(image_bytes, file.content_type)

    record_activity(
        db,
        current_user.profile_id,
        "PRESCRIPTION_SCANNED",
        f"AI scanned prescription: identified {len(result.get('medications', []))} potential medications",
        current_user
    )

    return result


@router.post("/parse-natural-language")
def parse_natural_language(
    payload: NaturalLanguageMedRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Translates phrases like:
    'Metformin 500mg morning and night after food for 30 days'
    into structured medication JSON.
    """
    return parse_natural_language_medication(payload.text)


@router.post("/check-interaction", response_model=DrugInteractionResponse)
def check_interactions(
    payload: DrugInteractionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates adverse drug-drug interactions and dietary precautions against current active medicines.
    """
    # Fetch current active medications
    active_meds = db.query(Medication).filter(
        Medication.profile_id == current_user.profile_id,
        Medication.is_active == True
    ).all()
    current_names = [f"{m.name} ({m.dosage})" for m in active_meds]

    if payload.current_medicines:
        current_names.extend(payload.current_medicines)

    result = check_drug_interaction(payload.new_medicine, current_names, lang=current_user.language)
    return result


@router.post("/weekly-summary", response_model=WeeklySummaryResponse)
def get_weekly_summary(
    send_email: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates an empathetic weekly health and adherence summary in English and Tamil.
    Optionally emails all family members.
    """
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    stats = calculate_adherence_stats(db, profile.id, days=7)
    now = datetime.now()
    appts = db.query(Appointment).filter(
        Appointment.profile_id == profile.id,
        Appointment.appointment_time >= now,
        Appointment.is_completed == False
    ).order_by(Appointment.appointment_time.asc()).limit(3).all()

    appt_strings = [
        f"Dr. {a.doctor_name} ({a.specialty}) on {a.appointment_time.strftime('%a, %b %d at %I:%M %p')}"
        for a in appts
    ]

    summary = generate_weekly_family_summary(
        elder_name=profile.full_name,
        adherence_pct=stats["adherence_percentage"],
        taken_count=stats["total_taken"],
        missed_count=stats["total_missed"],
        upcoming_appointments=appt_strings
    )

    start_d = (now - timedelta(days=7)).strftime("%b %d")
    end_d = now.strftime("%b %d, %Y")

    if send_email:
        family_members = db.query(ProfileMember).filter(
            ProfileMember.profile_id == profile.id
        ).all()
        # Group recipients by their saved language
        lang_groups = {}
        for m in family_members:
            if m.email:
                l = m.language or "en"
                lang_groups.setdefault(l, []).append(m.email)

        for l, emails in lang_groups.items():
            send_weekly_summary_email(
                recipients=emails,
                elder_name=profile.full_name,
                adherence_pct=stats["adherence_percentage"],
                summary_text_en=summary.get("friendly_summary_en", ""),
                summary_text_ta=summary.get("friendly_summary_ta", ""),
                summary_text_hi=summary.get("friendly_summary_hi", ""),
                upcoming_appts=appt_strings,
                lang=l
            )
        if family_members:
            record_activity(
                db,
                profile.id,
                "WEEKLY_SUMMARY_EMAILED",
                f"Weekly AI care summary emailed to {sum(len(e) for e in lang_groups.values())} recipients in their preferred languages",
                current_user
            )

    return WeeklySummaryResponse(
        start_date=start_d,
        end_date=end_d,
        elder_name=profile.full_name,
        adherence_percentage=stats["adherence_percentage"],
        taken_count=stats["total_taken"],
        missed_count=stats["total_missed"],
        upcoming_appointments=appt_strings,
        friendly_summary_en=summary.get("friendly_summary_en", ""),
        friendly_summary_ta=summary.get("friendly_summary_ta", ""),
        friendly_summary_hi=summary.get("friendly_summary_hi", ""),
        doctor_talking_points=summary.get("doctor_talking_points", [])
    )


@router.get("/recent-emails")
def get_sent_emails(current_user: CurrentUser = Depends(get_current_user)):
    """
    Live email audit inspector for hackathon demo.
    """
    return sent_email_history
