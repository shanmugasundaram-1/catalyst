import json
import logging
import re
from datetime import datetime, date, time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.services.gemini_service import get_gemini_client
from app.services.dose_service import get_today_doses, get_next_dose
from app.models import DoseLog, Medication, Appointment, Profile, ProfileMember
from app.services.email_service import send_sos_alert
from app.core.dependencies import record_activity, CurrentUser

logger = logging.getLogger("ayucare.voice")

def detect_language(query: str, default_lang: str = "en") -> str:
    """
    Detects Hindi (Devanagari), Tamil, or falls back to English / user preferred language.
    Also handles Tanglish and Hinglish by checking phonetics if needed.
    """
    # Hindi Devanagari range: \u0900-\u097F
    if re.search(r'[\u0900-\u097F]', query):
        return "hi"
    # Tamil script range: \u0B80-\u0BFF
    if re.search(r'[\u0B80-\u0BFF]', query):
        return "ta"
    
    q_lower = query.lower()
    # Tanglish indicators
    if any(w in q_lower for w in ["maathirai", "saapten", "saaptacha", "eppo", "naalaiku", "irukka", "illaya", "marunthu", "enaku"]):
        return "ta"
    # Hinglish indicators
    if any(w in q_lower for w in ["dawa", "le li", "le liya", "khali", "agla", "agli", "kab hai", "batao", "madad"]):
        return "hi"

    if default_lang in ["hi", "ta"]:
        return default_lang
    return "en"


def fuzzy_match_medicine(spoken_name: Optional[str], medications: List[Medication]) -> List[Medication]:
    """
    Matches spoken medicine name (or colloquial term like 'BP', 'Sugar') to active medications.
    """
    if not medications:
        return []
    if not spoken_name:
        return medications

    spoken = spoken_name.lower().strip()
    matches = []

    # Check common health condition aliases
    is_bp = any(term in spoken for term in ["bp", "blood pressure", "இரத்த அழுத்தம்", "ரத்த அழுத்தம்", "बीपी", "रक्तचाप"])
    is_sugar = any(term in spoken for term in ["sugar", "diabetes", "சர்க்கரை", "நீரிழிவு", "शुगर", "मधुमेह"])

    for med in medications:
        name_lower = med.name.lower()
        instr_lower = (med.instructions or "").lower()

        if is_bp and any(k in name_lower or k in instr_lower for k in ["telmisartan", "amlodipine", "losartan", "bp", "blood pressure"]):
            matches.append(med)
            continue
        if is_sugar and any(k in name_lower or k in instr_lower for k in ["metformin", "glimepiride", "sugar", "diabetes", "insulin"]):
            matches.append(med)
            continue

        # Substring / token matching
        tokens = [t for t in spoken.split() if len(t) > 2]
        if any(t in name_lower for t in tokens) or spoken in name_lower or name_lower in spoken:
            matches.append(med)

    return matches


def process_voice_intent(
    query: str,
    user_lang: str,
    profile_id: str,
    user_name: str,
    user_role: str,
    db: Session,
    confirmed_sos: bool = False
) -> Dict[str, Any]:
    """
    Processes natural voice commands in Hindi, Tamil, English (and Tanglish / Hinglish).
    Classifies intent into: MARK_DOSE_TAKEN, NEXT_DOSE_QUERY, APPOINTMENT_QUERY, SOS, UNKNOWN.
    Fuzzy matches medications, resolves ambiguities, verifies permissions, and executes actions.
    """
    detected_lang = detect_language(query, user_lang)
    lang = detected_lang if detected_lang in ["hi", "ta", "en"] else (user_lang or "en")

    intent: Optional[str] = None
    target_medicine: Optional[str] = None
    is_sos_confirmation: bool = confirmed_sos

    # Check for direct confirmation phrase
    q_lower = query.lower().strip()
    if any(q_lower == p or p in q_lower for p in ["yes send sos", "send sos", "confirm sos", "हाँ भेजो", "भेज दो", "ஆம் அனுப்பு", "ஆம் அவசரம்", "confirm"]):
        is_sos_confirmation = True

    # 1. Attempt classification with Gemini API structured prompt
    client = get_gemini_client()
    if client:
        try:
            prompt = f"""
You are an expert multilingual voice AI assistant for an elderly healthcare application (AyuCare).
User Query: "{query}"

Understand languages and code-mixing: English, Tamil (தமிழ் & Tanglish), Hindi (हिन्दी & Hinglish).
Classify into ONE canonical intent:
- MARK_DOSE_TAKEN: user states they took/swallowed their medication (e.g., "I took my BP tablet", "BP maathirai saapten", "मैंने बीपी की दवा ले ली", "Metformin potten")
- NEXT_DOSE_QUERY: user asks when their next medicine is due (e.g., "When is my next dose?", "Next maathirai eppo?", "अगली दवा कब है?")
- APPOINTMENT_QUERY: user asks about upcoming doctor visits (e.g., "Do I have an appointment tomorrow?", "Naalaiku doctor appointment irukka?", "कल डॉक्टर का अपॉइंटमेंट है क्या?")
- SOS: user requests urgent emergency help (e.g., "Emergency", "I need help", "Avasaram", "அவசரம்", "मदद चाहिए", "अस्पताल बुलाओ")
- UNKNOWN: greetings, general chatter, or unrecognized intent

Return ONLY a valid JSON object matching this schema:
{{
  "intent": "MARK_DOSE_TAKEN | NEXT_DOSE_QUERY | APPOINTMENT_QUERY | SOS | UNKNOWN",
  "target_medicine": "extracted medicine name or condition like BP/Sugar if mentioned, else null"
}}
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            parsed = json.loads(raw.strip())
            intent = parsed.get("intent")
            target_medicine = parsed.get("target_medicine")
        except Exception as e:
            logger.error(f"Gemini voice classification failed: {e}. Using deterministic multilingual fallback.")

    # 2. Multilingual regex & rule-based fallback
    if not intent or intent == "UNKNOWN":
        # Check SOS
        if any(w in query for w in ["मदद", "अस्पताल", "इमरजेंसी", "एसओएस", "बचाओ"]) or \
           any(w in query for w in ["உதவி", "அவசரம்", "காப்பாத்து"]) or \
           any(w in q_lower for w in ["emergency", "sos", "help me", "ambulance", "avasaram"]):
            intent = "SOS"

        # Check Mark Dose Taken
        elif any(w in query for w in ["ले ली", "दवा खा ली", "दवा ले ली", "पी ली", "खा लिया", "ले लिया"]) or \
             any(w in query for w in ["சாப்பிட்டேன்", "போட்டுட்டேன்", "எடுத்துக்கிட்டேன்", "சாப்பிட்டாச்சு", "போட்டேன்"]) or \
             any(w in q_lower for w in ["took", "taken", "had my", "saapten", "potten", "saaptacha", "dawa le li", "swallowed"]):
            intent = "MARK_DOSE_TAKEN"
            if any(w in query or w in q_lower for w in ["बीपी", "bp", "இரத்த அழுத்தம்", "blood pressure"]):
                target_medicine = "BP"
            elif any(w in query or w in q_lower for w in ["शुगर", "sugar", "சர்க்கரை", "diabetes", "metformin"]):
                target_medicine = "Metformin"

        # Check Next Dose Query
        elif any(w in query for w in ["अगली दवा", "अगला खुराक", "कब दवा", "दवा का समय"]) or \
             any(w in query for w in ["அடுத்த மருந்து", "அடுத்த மாத்திரை", "எப்போ மருந்து"]) or \
             any(w in q_lower for w in ["next dose", "next medicine", "when is my medicine", "upcoming medicine", "next maathirai", "eppo"]):
            intent = "NEXT_DOSE_QUERY"

        # Check Appointment Query
        elif any(w in query for w in ["अपॉइंटमेंट", "डॉक्टर", "दिखाना"]) or \
             any(w in query for w in ["அப்பாயிண்ட்மென்ட்", "டாக்டர்", "மருத்துவர்"]) or \
             any(w in q_lower for w in ["appointment", "doctor", "visit", "irukka", "hospital"]):
            intent = "APPOINTMENT_QUERY"
        else:
            intent = "UNKNOWN"

    # Action execution
    action_performed = None
    requires_confirmation = False
    data = {}
    reply_text = ""

    # Current user mock object for activity logging
    class MockCurrentUser:
        def __init__(self, name, role, email, profile_id):
            self.name = name
            self.role = role
            self.email = email
            self.profile_id = profile_id
            self.language = lang

    acting_user = MockCurrentUser(user_name, user_role, f"{user_name.lower()}@voice.user", profile_id)

    # --- INTENT: MARK_DOSE_TAKEN ---
    if intent == "MARK_DOSE_TAKEN":
        # Verify role permissions: Only ELDER and CARETAKER can record dose actions
        if user_role == "FAMILY":
            if lang == "hi":
                reply_text = "परिवार के सदस्यों के पास केवल देखने की अनुमति है। कृपया खुराक दर्ज करने के लिए बुजुर्ग या देखभालकर्ता से कहें।"
            elif lang == "ta":
                reply_text = "குடும்ப உறுப்பினர்களுக்கு பார்க்கும் உரிமை மட்டுமே உள்ளது. மருந்தைப் பதிவு செய்ய தாத்தா அல்லது பராமரிப்பாளரைக் கேட்கவும்."
            else:
                reply_text = "Family members have observer access only. Please ask the elder or primary caretaker to record doses."
            return {
                "intent": "MARK_DOSE_TAKEN",
                "reply_text": reply_text,
                "spoken_language": lang,
                "action_performed": None,
                "requires_confirmation": False,
                "data": {}
            }

        # Fetch today's doses
        today_doses = get_today_doses(db, profile_id)
        pending_doses = [d for d in today_doses if d.status == "PENDING"]

        if not pending_doses:
            if lang == "hi":
                reply_text = "आज के लिए आपकी सभी निर्धारित दवाएं पहले ही ली जा चुकी हैं। बहुत बढ़िया!"
            elif lang == "ta":
                reply_text = "இன்றைய அனைத்து மருந்துகளும் ஏற்கனவே எடுக்கப்பட்டுவிட்டன. அருமை!"
            else:
                reply_text = "All scheduled doses for today have already been marked as taken. Well done!"
            return {
                "intent": "MARK_DOSE_TAKEN",
                "reply_text": reply_text,
                "spoken_language": lang,
                "action_performed": None,
                "requires_confirmation": False,
                "data": {}
            }

        # Fuzzy match target medicine
        active_meds = db.query(Medication).filter(Medication.profile_id == profile_id, Medication.is_active == True).all()
        matched_meds = fuzzy_match_medicine(target_medicine, active_meds) if target_medicine else []

        # Check for ambiguity if user did not specify and multiple different medicines are pending
        distinct_pending_med_ids = list(set(d.medication_id for d in pending_doses))
        if len(distinct_pending_med_ids) > 1 and not target_medicine:
            med_names = [d.medication.name for d in pending_doses[:2] if d.medication]
            if lang == "hi":
                reply_text = f"आपके पास एक से अधिक लंबित दवाएं हैं। क्या आपका मतलब {med_names[0]} है या {med_names[1]}?"
            elif lang == "ta":
                reply_text = f"தற்போது பல மருந்துகள் காத்திருக்கின்றன. நீங்கள் {med_names[0]}-ஐ குறிப்பிடுகிறீர்களா அல்லது {med_names[1]}-ஐயா?"
            else:
                reply_text = f"You have multiple pending doses. Did you take {med_names[0]} or {med_names[1]}?"
            return {
                "intent": "MARK_DOSE_TAKEN",
                "reply_text": reply_text,
                "spoken_language": lang,
                "action_performed": None,
                "requires_confirmation": False,
                "data": {"pending_options": med_names}
            }

        # Select candidate dose
        candidate_dose = None
        if matched_meds:
            matched_ids = [m.id for m in matched_meds]
            candidate_dose = next((d for d in pending_doses if d.medication_id in matched_ids), None)
        if not candidate_dose:
            candidate_dose = pending_doses[0]

        # Execute dose mark
        candidate_dose.status = "TAKEN"
        candidate_dose.taken_at = datetime.now()
        candidate_dose.taken_by_name = f"{user_name} (Voice)"
        med = candidate_dose.medication
        if med and med.stock_count > 0:
            med.stock_count -= 1
        db.commit()

        action_performed = f"Marked {med.name if med else 'dose'} as TAKEN via voice"
        data = {"dose_id": candidate_dose.id, "medication_name": med.name if med else "Medicine"}

        # Record activity
        record_activity(
            db,
            profile_id,
            "VOICE_DOSE_RECORDED",
            f"Voice command marked {med.name} ({med.dosage}) as taken by {user_name}",
            acting_user
        )

        if lang == "hi":
            reply_text = f"बहुत बढ़िया! आपकी दवा {med.name} ({med.dosage}) सफलतापूर्वक दर्ज कर ली गई है।"
        elif lang == "ta":
            reply_text = f"மிக நன்று! உங்கள் மருந்து {med.name} ({med.dosage}) எடுக்கப்பட்டதாக பதிவு செய்யப்பட்டது."
        else:
            reply_text = f"Wonderful! Your dose of {med.name} ({med.dosage}) has been recorded as taken."

    # --- INTENT: NEXT_DOSE_QUERY ---
    elif intent == "NEXT_DOSE_QUERY":
        next_d = get_next_dose(db, profile_id)
        if next_d and next_d.medication:
            med = next_d.medication
            t_str = next_d.scheduled_time.strftime("%I:%M %p")
            data = {
                "medication_name": med.name,
                "dosage": med.dosage,
                "scheduled_time": t_str,
                "food_timing": med.food_timing
            }
            food_hi = "खाने के बाद" if med.food_timing == "AFTER_FOOD" else ("खाने से पहले" if med.food_timing == "BEFORE_FOOD" else "भोजन के साथ")
            food_ta = "சாப்பிட்ட பிறகு" if med.food_timing == "AFTER_FOOD" else ("சாப்பிடுவதற்கு முன்" if med.food_timing == "BEFORE_FOOD" else "உணவுடன்")
            food_en = "after food" if med.food_timing == "AFTER_FOOD" else ("before food" if med.food_timing == "BEFORE_FOOD" else "")

            if lang == "hi":
                reply_text = f"आपकी अगली दवा {med.name} ({med.dosage}) समय {t_str} पर {food_hi} लेनी है।"
            elif lang == "ta":
                reply_text = f"உங்கள் அடுத்த மருந்து {med.name} ({med.dosage}) நேரம் {t_str}-க்கு {food_ta} எடுக்க வேண்டும்."
            else:
                reply_text = f"Your next dose is {med.name} ({med.dosage}) scheduled for {t_str} ({food_en})."
        else:
            if lang == "hi":
                reply_text = "आज के लिए कोई आगामी खुराक बाकी नहीं है। आप आराम करें।"
            elif lang == "ta":
                reply_text = "இன்றைக்கு இனி மருந்து எதுவும் இல்லை. ஓய்வெடுக்கலாம்."
            else:
                reply_text = "You have no upcoming doses scheduled for today. Rest well!"

    # --- INTENT: APPOINTMENT_QUERY ---
    elif intent == "APPOINTMENT_QUERY":
        now = datetime.now()
        appts = db.query(Appointment).filter(
            Appointment.profile_id == profile_id,
            Appointment.appointment_time >= now,
            Appointment.is_completed == False
        ).order_by(Appointment.appointment_time.asc()).first()

        if appts:
            dt_str = appts.appointment_time.strftime("%A, %d %B at %I:%M %p")
            data = {
                "doctor_name": appts.doctor_name,
                "specialty": appts.specialty,
                "time": dt_str,
                "location": appts.location
            }
            if lang == "hi":
                reply_text = f"हाँ, आपका अगला अपॉइंटमेंट डॉ. {appts.doctor_name} ({appts.specialty}) के साथ {dt_str} को {appts.location} में है।"
            elif lang == "ta":
                reply_text = f"உங்கள் அடுத்த மருத்துவ சந்திப்பு டாக்டர் {appts.doctor_name} ({appts.specialty}) உடன் {dt_str} அன்று {appts.location}-ல் உள்ளது."
            else:
                reply_text = f"Your next appointment is with Dr. {appts.doctor_name} ({appts.specialty}) on {dt_str} at {appts.location}."
        else:
            if lang == "hi":
                reply_text = "आपके पास आने वाले दिनों में कोई डॉक्टर अपॉइंटमेंट निर्धारित नहीं है।"
            elif lang == "ta":
                reply_text = "தற்போது திட்டமிடப்பட்ட மருத்துவ சந்திப்புகள் எதுவும் இல்லை."
            else:
                reply_text = "You have no upcoming doctor appointments scheduled."

    # --- INTENT: SOS ---
    elif intent == "SOS":
        if not is_sos_confirmation:
            # Ask for voice or tap confirmation first
            requires_confirmation = True
            if lang == "hi":
                reply_text = "क्या आप आपातकालीन SOS अलर्ट भेजना चाहते हैं? कृपया 'हाँ भेजो' कहें या पुष्टि बटन दबाएं।"
            elif lang == "ta":
                reply_text = "நீங்கள் அவசர SOS எச்சரிக்கை அனுப்ப விரும்புகிறீர்களா? 'ஆம் அனுப்பு' என கூறவும் அல்லது பொத்தானை அழுத்தவும்."
            else:
                reply_text = "Are you sure you want to broadcast an Emergency SOS alert? Please tap Confirm or say 'Yes, send SOS'."
        else:
            # Confirmed: dispatch SOS emails to caretaker and family in their language
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            members = db.query(ProfileMember).filter(
                ProfileMember.profile_id == profile_id,
                ProfileMember.role.in_(["CARETAKER", "FAMILY"])
            ).all()

            lang_groups = {}
            for m in members:
                if m.email:
                    mlang = m.language or "en"
                    lang_groups.setdefault(mlang, []).append(m.email)

            now_str = datetime.now().strftime("%A, %B %d at %I:%M %p")
            for mlang, emails in lang_groups.items():
                send_sos_alert(
                    recipients=emails,
                    elder_name=profile.full_name if profile else "Elder",
                    timestamp_str=now_str,
                    emergency_phone=profile.emergency_phone if profile else "",
                    notes="Voice-confirmed Emergency SOS",
                    lang=mlang
                )

            action_performed = "Dispatched Emergency SOS broadcast via voice"
            record_activity(
                db,
                profile_id,
                "EMERGENCY_SOS_VOICE",
                f"Emergency SOS broadcast dispatched via voice by {user_name}",
                acting_user
            )

            if lang == "hi":
                reply_text = "आपातकालीन चेतावनी आपके देखभालकर्ता और परिवार को तुरंत भेज दी गई है। सहायता आ रही है।"
            elif lang == "ta":
                reply_text = "அவசர உதவி எச்சரிக்கை உடனே உங்கள் பராமரிப்பாளர் மற்றும் குடும்பத்தினருக்கு அனுப்பப்பட்டது. உதவி வருகிறது."
            else:
                reply_text = "Emergency alert has been sent to your caretaker and family members. Stay calm, help is informed."

    # --- INTENT: UNKNOWN ---
    else:
        if lang == "hi":
            reply_text = f"नमस्ते {user_name}! मैं आपका स्वास्थ्य सहायक हूँ। आप कह सकते हैं: 'मैंने बीपी की दवा ले ली', 'अगली दवा कब है?' या 'डॉक्टर का अपॉइंटमेंट है क्या?'"
        elif lang == "ta":
            reply_text = f"வணக்கம் {user_name}! நான் உங்கள் நலன் உதவியாளர். 'மாத்திரை சாப்பிட்டேன்', 'அடுத்த மருந்து எப்போ?' அல்லது 'டாக்டர் சந்திப்பு இருக்கா?' என கேட்கலாம்."
        else:
            reply_text = f"Hello {user_name}! I am your care assistant. You can tell me 'I took my BP tablet', ask 'When is my next dose?', or check 'Do I have an appointment?'"

    return {
        "intent": intent,
        "reply_text": reply_text,
        "spoken_language": lang,
        "action_performed": action_performed,
        "requires_confirmation": requires_confirmation,
        "data": data
    }
