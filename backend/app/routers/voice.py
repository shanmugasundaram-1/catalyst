from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, CurrentUser
from app.schemas import VoiceIntentRequest, VoiceIntentResponse
from app.services.voice_service import process_voice_intent

router = APIRouter(prefix="/api/voice", tags=["Multilingual Voice Assistant"])

@router.post("/intent", response_model=VoiceIntentResponse)
def handle_voice_intent(
    payload: VoiceIntentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Multilingual Voice Assistant API (Hindi, Tamil, English):
    Processes natural voice commands like:
    - Hindi: 'मैंने बीपी की दवा ले ली', 'अगली दवा कब है?', 'कल डॉक्टर का अपॉइंटमेंट है क्या?'
    - Tamil: 'நான் பிபி மாத்திரை போட்டுட்டேன்', 'அடுத்த மருந்து எப்போ?'
    - English: 'I took my BP medicine', 'When is my next dose?'
    and performs the corresponding clinical action while replying in the same language.
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Voice query cannot be empty")

    user_preferred_lang = payload.language or current_user.language or "en"

    result = process_voice_intent(
        query=payload.query.strip(),
        user_lang=user_preferred_lang,
        profile_id=current_user.profile_id,
        user_name=current_user.name,
        user_role=current_user.role,
        db=db,
        confirmed_sos=payload.confirmed_sos or False
    )

    return VoiceIntentResponse(
        intent=result["intent"],
        reply_text=result["reply_text"],
        spoken_language=result["spoken_language"],
        action_performed=result["action_performed"],
        requires_confirmation=result.get("requires_confirmation", False),
        data=result["data"]
    )
