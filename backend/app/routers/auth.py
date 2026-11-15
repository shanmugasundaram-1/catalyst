import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_passcode, verify_passcode, create_access_token
from app.core.dependencies import get_current_user, record_activity
from app.models import Profile, ProfileMember
from app.schemas import JoinProfileRequest, CreateProfileRequest, TokenResponse, CurrentUser
from app.services.dose_service import ensure_doses_generated_for_date
from datetime import date

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

@router.post("/join", response_model=TokenResponse)
def join_profile(payload: JoinProfileRequest, db: Session = Depends(get_db)):
    """
    Join an elder profile using profile_id and role passcode.
    Role is automatically resolved from passcode:
    - Matches elder_passcode -> ELDER
    - Matches caretaker_passcode -> CARETAKER
    - Matches family_passcode -> FAMILY
    """
    profile = db.query(Profile).filter(Profile.id == payload.profile_id.strip()).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{payload.profile_id}' not found. Please verify the Profile ID."
        )

    resolved_role = None
    passcode = payload.passcode.strip()

    if verify_passcode(passcode, profile.elder_passcode_hash):
        resolved_role = "ELDER"
    elif verify_passcode(passcode, profile.caretaker_passcode_hash):
        resolved_role = "CARETAKER"
    elif verify_passcode(passcode, profile.family_passcode_hash):
        resolved_role = "FAMILY"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passcode for this elder profile. Check with the profile creator."
        )

    # Upsert ProfileMember entry
    member = db.query(ProfileMember).filter(
        ProfileMember.profile_id == profile.id,
        ProfileMember.email == payload.email.lower().strip()
    ).first()

    chosen_lang = payload.language or (member.language if member else profile.language) or "en"

    if member:
        member.role = resolved_role
        member.name = payload.name.strip()
        if payload.language:
            member.language = payload.language
        if payload.phone:
            member.phone = payload.phone.strip()
    else:
        member = ProfileMember(
            profile_id=profile.id,
            role=resolved_role,
            name=payload.name.strip(),
            email=payload.email.lower().strip(),
            phone=payload.phone.strip() if payload.phone else "",
            language=chosen_lang
        )
        db.add(member)
    db.commit()

    # Pre-generate today's doses if needed
    ensure_doses_generated_for_date(db, profile.id, date.today())

    # Create token
    token_claims = {
        "sub": profile.id,
        "role": resolved_role,
        "name": payload.name.strip(),
        "email": payload.email.lower().strip()
    }
    access_token = create_access_token(token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=resolved_role,
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        profile_id=profile.id,
        profile_name=profile.full_name,
        language=member.language or "en",
        auto_approve_caretaker=profile.auto_approve_caretaker
    )


@router.post("/register-profile", response_model=TokenResponse)
def register_profile(payload: CreateProfileRequest, db: Session = Depends(get_db)):
    """
    Registers a new Elder Profile with designated passcodes for Elder, Caretaker, and Family roles.
    """
    # Create readable profile ID, e.g. ELDER-xxxx
    short_id = f"ELDER-{uuid.uuid4().hex[:6].upper()}"

    new_profile = Profile(
        id=short_id,
        full_name=payload.full_name.strip(),
        age=payload.age,
        blood_group=payload.blood_group.strip(),
        emergency_phone=payload.emergency_phone.strip(),
        emergency_notes=payload.emergency_notes.strip(),
        elder_passcode_hash=hash_passcode(payload.elder_passcode.strip()),
        caretaker_passcode_hash=hash_passcode(payload.caretaker_passcode.strip()),
        family_passcode_hash=hash_passcode(payload.family_passcode.strip()),
        auto_approve_caretaker=payload.auto_approve_caretaker,
        language=payload.language
    )
    db.add(new_profile)
    db.commit()

    # Add creator as member (default role ELDER if creating)
    creator_member = ProfileMember(
        profile_id=short_id,
        role="ELDER",
        name=payload.creator_name.strip(),
        email=payload.creator_email.lower().strip(),
        phone=payload.emergency_phone.strip()
    )
    db.add(creator_member)
    db.commit()

    token_claims = {
        "sub": short_id,
        "role": "ELDER",
        "name": payload.creator_name.strip(),
        "email": payload.creator_email.lower().strip()
    }
    access_token = create_access_token(token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role="ELDER",
        name=payload.creator_name.strip(),
        email=payload.creator_email.lower().strip(),
        profile_id=short_id,
        profile_name=payload.full_name.strip(),
        language=payload.language,
        auto_approve_caretaker=payload.auto_approve_caretaker
    )


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user
