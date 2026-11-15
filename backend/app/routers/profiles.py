from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_passcode
from app.core.dependencies import get_current_user, require_roles, record_activity
from app.models import Profile, ProfileMember
from app.schemas import ProfileResponse, ProfileSettingsUpdate, CurrentUser, UpdateMemberLanguageRequest

router = APIRouter(prefix="/api/profiles", tags=["Profile & Settings"])

@router.patch("/member-language")
def update_member_language(
    payload: UpdateMemberLanguageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the saved language preference ('en', 'ta', 'hi') for the current user.
    Alert emails and voice assistant will use this saved language.
    """
    lang = payload.language.lower().strip()
    if lang not in ["en", "ta", "hi"]:
        raise HTTPException(status_code=400, detail="Supported languages are 'en', 'ta', 'hi'")

    member = db.query(ProfileMember).filter(
        ProfileMember.profile_id == current_user.profile_id,
        ProfileMember.email == current_user.email.lower().strip()
    ).first()

    if member:
        member.language = lang

    if current_user.role == "ELDER":
        profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
        if profile:
            profile.language = lang

    db.commit()

    record_activity(
        db,
        current_user.profile_id,
        "LANGUAGE_UPDATED",
        f"{current_user.name} changed language preference to '{lang}'",
        current_user
    )

    return {"status": "SUCCESS", "language": lang, "message": f"Language preference set to {lang}"}

@router.get("/current", response_model=ProfileResponse)
def get_current_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/current", response_model=ProfileResponse)
def update_profile_settings(
    update_data: ProfileSettingsUpdate,
    current_user: CurrentUser = Depends(require_roles(["ELDER"])),
    db: Session = Depends(get_db)
):
    """
    Update elder settings (only ELDER can perform this).
    Allows toggling auto_approve_caretaker, changing passcodes, updating emergency contact, etc.
    """
    profile = db.query(Profile).filter(Profile.id == current_user.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if update_data.full_name is not None:
        profile.full_name = update_data.full_name
    if update_data.age is not None:
        profile.age = update_data.age
    if update_data.blood_group is not None:
        profile.blood_group = update_data.blood_group
    if update_data.emergency_phone is not None:
        profile.emergency_phone = update_data.emergency_phone
    if update_data.emergency_notes is not None:
        profile.emergency_notes = update_data.emergency_notes
    if update_data.auto_approve_caretaker is not None:
        profile.auto_approve_caretaker = update_data.auto_approve_caretaker
    if update_data.language is not None:
        profile.language = update_data.language

    # Passcode updates
    if update_data.elder_passcode:
        profile.elder_passcode_hash = hash_passcode(update_data.elder_passcode.strip())
    if update_data.caretaker_passcode:
        profile.caretaker_passcode_hash = hash_passcode(update_data.caretaker_passcode.strip())
    if update_data.family_passcode:
        profile.family_passcode_hash = hash_passcode(update_data.family_passcode.strip())

    db.commit()
    db.refresh(profile)

    record_activity(
        db,
        profile.id,
        "SETTINGS_UPDATED",
        f"Elder updated profile settings (Auto-approve caretaker: {profile.auto_approve_caretaker})",
        current_user
    )

    return profile
