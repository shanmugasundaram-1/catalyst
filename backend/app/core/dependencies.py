from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Profile, ProfileMember, ActivityLog
from app.schemas import CurrentUser

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    profile_id = payload.get("sub")
    role = payload.get("role")
    name = payload.get("name", "User")
    email = payload.get("email", "")

    if not profile_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims.",
        )

    # Verify profile exists
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elder profile not found.",
        )

    # Fetch member language preference
    member = db.query(ProfileMember).filter(
        ProfileMember.profile_id == profile_id,
        ProfileMember.email == email.lower().strip()
    ).first()
    user_lang = member.language if (member and member.language) else (profile.language or "en")

    return CurrentUser(
        profile_id=profile_id,
        role=role,
        name=name,
        email=email,
        language=user_lang
    )

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}. Your role is {current_user.role}."
            )
        return current_user
    return role_checker

def record_activity(
    db: Session,
    profile_id: str,
    action: str,
    details: str,
    user: CurrentUser
):
    log = ActivityLog(
        profile_id=profile_id,
        action=action,
        details=details,
        performed_by_name=user.name,
        performed_by_role=user.role
    )
    db.add(log)
    db.commit()
