import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Profile, ProfileMember, DoseLog, Medication, Appointment, CareInsight
from app.services.gemini_service import get_gemini_client
from app.services.email_service import send_care_insight_email
from app.core.database import SessionLocal

logger = logging.getLogger("ayucare.insights")

def generate_ai_insight_text(
    elder_name: str,
    insight_type: str,
    details: Dict[str, Any]
) -> Dict[str, str]:
    """
    Calls Gemini to write a warm, plain-language care insight with one suggested action in en, ta, and hi.
    Includes a doctor consultation disclaimer note. Falls back to deterministic templates.
    """
    client = get_gemini_client()
    if client:
        try:
            prompt = f"""
You are an expert, compassionate geriatric care AI assistant.
Elder Name: {elder_name}
Insight Type: {insight_type}
Observed Data Details: {json.dumps(details)}

Write a warm, non-judgmental, easy-to-understand health observation for the family & caretaker.
Provide ONE practical suggested action.
Add a gentle note that this is not medical advice and to consult their prescribing doctor if needed.
Generate the result in English, Tamil (தமிழ்), and Hindi (हिन्दी).

Return ONLY valid JSON matching this schema:
{{
  "title_en": "Short clear title in English",
  "title_ta": "Short clear title in Tamil",
  "title_hi": "Short clear title in Hindi",
  "text_en": "2-3 sentences warm explanation in English",
  "text_ta": "2-3 sentences warm explanation in Tamil",
  "text_hi": "2-3 sentences warm explanation in Hindi",
  "suggested_action_en": "Single actionable recommendation in English",
  "suggested_action_ta": "Single actionable recommendation in Tamil",
  "suggested_action_hi": "Single actionable recommendation in Hindi"
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
            return json.loads(raw.strip())
        except Exception as e:
            logger.error(f"Gemini insight generation failed: {e}. Using multilingual templates.")

    # Rule-based multilingual fallback templates
    if insight_type == "REPEATED_MISSES":
        slot = details.get("slot_time", "evening")
        med = details.get("med_name", "prescribed medicine")
        return {
            "title_en": f"Pattern: Repeated Missed Doses at {slot}",
            "title_ta": f"கவனத்திற்கு: {slot} நேர மருந்து தொடர்ந்து தவறவிடப்பட்டுள்ளது",
            "title_hi": f"सतर्कता: समय {slot} की खुराक लगातार छूट रही है",
            "text_en": f"{elder_name} missed their {med} dose around {slot} on 3 or more occasions recently. Evening fatigue or post-dinner routine changes often cause this. Always consult your doctor before modifying medication schedules.",
            "text_ta": f"{elder_name} சமீபத்தில் {slot} நேர {med} மருந்தை 3 முறைக்கு மேல் தவறவிட்டுள்ளார். இரவு நேர சோர்வு இதற்கு காரணமாக இருக்கலாம். அட்டவணையை மாற்ற மருத்துவரிடம் ஆலோசனை பெறவும்.",
            "text_hi": f"{elder_name} ने हाल ही में {slot} बजे की {med} दवा 3 से अधिक बार छोड़ दी है। शाम की थकान या व्यस्तता इसका कारण हो सकती है। दवा समय बदलने से पहले डॉक्टर से परामर्श अवश्य लें।",
            "suggested_action_en": f"Align {med} with dinner or set a dedicated family reminder call at {slot}.",
            "suggested_action_ta": f"இரவு உணவோடு மருந்தை இணைக்கவும் அல்லது குடும்பத்தினர் அந்த நேரத்தில் நினைவூட்டவும்.",
            "suggested_action_hi": f"दवा को रात के खाने के तुरंत साथ लें या परिवार से एक याद दिलाने वाली कॉल का समय तय करें।"
        }

    elif insight_type == "ADHERENCE_DROP":
        prev = details.get("prev_pct", 90)
        curr = details.get("curr_pct", 65)
        return {
            "title_en": f"Adherence Dip Alert ({prev}% → {curr}%)",
            "title_ta": f"மருந்து உட்கொள்ளல் குறைவு ({prev}% → {curr}%)",
            "title_hi": f"नियमितता में गिरावट सूचना ({prev}% → {curr}%)",
            "text_en": f"{elder_name}'s medication adherence dropped from {prev}% to {curr}% over the last week. Sudden adherence drops can signal mild discomfort, swallowing difficulty, or routine disruptions.",
            "text_ta": f"{elder_name} அவர்களின் கடந்த வார மருந்து உட்கொள்ளல் விகிதம் {prev}%-லிருந்து {curr}%-ஆக குறைந்துள்ளது. உடல்நல சோர்வு அல்லது சுலபமாக விழுங்க முடியாதது காரணமாக இருக்கலாம்.",
            "text_hi": f"{elder_name} की साप्ताहिक दवा नियमितता {prev}% से गिरकर {curr}% हो गई है। यह किसी शारीरिक असुविधा या दिनचर्या में बदलाव का संकेत हो सकता है।",
            "suggested_action_en": "Schedule a gentle check-in call to review if any pill causes stomach upset or side effects.",
            "suggested_action_ta": "மருந்து சாப்பிடுவதில் சிரமம் அல்லது பக்கவிளைவுகள் உள்ளதா என்று அன்புடன் கேட்டு அறியவும்.",
            "suggested_action_hi": "बुजुर्ग से बात करके पता करें कि क्या किसी दवा से पेट में परेशानी या निगलने में कठिनाई हो रही है।"
        }

    elif insight_type == "LOW_STOCK":
        med = details.get("med_name", "Essential Medication")
        days = details.get("days_left", 2)
        stock = details.get("stock", 3)
        return {
            "title_en": f"Low Stock: Refill Needed for {med}",
            "title_ta": f"மருந்து கையிருப்பு குறைவு: {med}",
            "title_hi": f"दवा कम है: {med} दोबारा मंगवाएं",
            "text_en": f"{elder_name} has only {stock} doses ({days} days) of {med} remaining. Running out of maintenance medication may disrupt blood pressure or glycemic control.",
            "text_ta": f"{elder_name} அவர்களிடம் {med} மருந்து {stock} மாத்திரைகள் ({days} நாட்களுக்கு மட்டுமே) உள்ளது. உடனே மறுஆர்டர் செய்யவும்.",
            "text_hi": f"{elder_name} के पास {med} की केवल {stock} खुराकें ({days} दिनों के लिए) बची हैं। नियमित दवा खत्म होने से बीपी या शुगर का स्तर प्रभावित हो सकता है।",
            "suggested_action_en": f"Order a prescription refill for {med} from your local pharmacy today.",
            "suggested_action_ta": f"{med} மருந்தை இன்றே மருந்தகத்தில் இருந்து மறுஆர்டர் செய்து கொள்ளவும்.",
            "suggested_action_hi": f"आज ही नज़दीकी मेडिकल स्टोर से {med} का नया पत्ता मंगवा लें।"
        }

    else:
        # Default / Appointment unconfirmed
        doctor = details.get("doctor_name", "Doctor")
        appt_time = details.get("appt_time", "soon")
        return {
            "title_en": f"Upcoming Consultation Reminder: Dr. {doctor}",
            "title_ta": f"மருத்துவ சந்திப்பு நினைவூட்டல்: டாக்டர் {doctor}",
            "title_hi": f"डॉक्टर परामर्श सूचना: डॉ. {doctor}",
            "text_en": f"{elder_name} has an upcoming medical consultation with Dr. {doctor} on {appt_time}. Ensure lab test reports and current medicine strips are ready.",
            "text_ta": f"{elder_name} அவர்களுக்கு டாக்டர் {doctor} உடன் {appt_time} அன்று மருத்துவ சந்திப்பு உள்ளது. முந்தைய பரிசோதனை முடிவுகளை தயார் செய்து கொள்ளவும்.",
            "text_hi": f"{elder_name} का डॉ. {doctor} के साथ {appt_time} को परामर्श निर्धारित है। पिछली रिपोर्ट और दवाओं के पत्ते साथ रखना सुनिश्चित करें।",
            "suggested_action_en": "Confirm ride/companion arrangements and gather current blood pressure/sugar logs.",
            "suggested_action_ta": "பயண ஏற்பாட்டை உறுதி செய்து, முந்தைய ரத்த அழுத்த அளவுகளை குறித்து வைக்கவும்.",
            "suggested_action_hi": "जाने की व्यवस्था सुनिश्चित करें और बीपी/शुगर की रीडिंग डायरी में नोट कर लें।"
        }


def analyze_profile_insights(
    db: Session,
    profile_id: str,
    trigger_notifications: bool = True
) -> List[CareInsight]:
    """
    Analyses the elder's last 14 days of dose logs for early warning patterns:
    1. Repeated misses at same time slot (3+ days)
    2. Adherence drop of > 20% vs previous week
    3. Medicine stock running out within 3 days
    4. Unacknowledged / upcoming appointment
    Prevents duplicates within 48 hours and emails caretaker + family in their language.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        return []

    now = datetime.now()
    cutoff_14d = now - timedelta(days=14)
    cutoff_7d = now - timedelta(days=7)
    cutoff_48h = now - timedelta(hours=48)

    created_insights = []

    # 1. Check Repeated Misses of Same Time Slot (3+ days)
    recent_doses_14d = db.query(DoseLog).filter(
        DoseLog.profile_id == profile_id,
        DoseLog.scheduled_time >= cutoff_14d
    ).all()

    missed_doses = [d for d in recent_doses_14d if d.status == "MISSED"]
    # Group by slot time string e.g. "20:30"
    slot_miss_counts: Dict[str, List[DoseLog]] = {}
    for d in missed_doses:
        t_slot = d.scheduled_time.strftime("%I:%M %p")
        slot_miss_counts.setdefault(t_slot, []).append(d)

    for slot, d_list in slot_miss_counts.items():
        if len(d_list) >= 3:
            # Check duplicate within 48h
            existing = db.query(CareInsight).filter(
                CareInsight.profile_id == profile_id,
                CareInsight.insight_type == "REPEATED_MISSES",
                CareInsight.created_at >= cutoff_48h
            ).first()

            if not existing:
                med_name = d_list[0].medication.name if d_list[0].medication else "Medicine"
                ai_texts = generate_ai_insight_text(
                    profile.full_name,
                    "REPEATED_MISSES",
                    {"slot_time": slot, "med_name": med_name, "miss_count": len(d_list)}
                )
                insight = CareInsight(
                    profile_id=profile_id,
                    insight_type="REPEATED_MISSES",
                    severity="warning",
                    title_en=ai_texts["title_en"],
                    title_ta=ai_texts["title_ta"],
                    title_hi=ai_texts["title_hi"],
                    text_en=ai_texts["text_en"],
                    text_ta=ai_texts["text_ta"],
                    text_hi=ai_texts["text_hi"],
                    suggested_action=ai_texts["suggested_action_en"],
                    suggested_action_ta=ai_texts["suggested_action_ta"],
                    suggested_action_hi=ai_texts["suggested_action_hi"],
                    status="ACTIVE"
                )
                db.add(insight)
                db.commit()
                db.refresh(insight)
                created_insights.append(insight)
            break

    # 2. Check Adherence Drop > 20% vs Previous Week
    week1_doses = [d for d in recent_doses_14d if d.scheduled_time < cutoff_7d]
    week2_doses = [d for d in recent_doses_14d if d.scheduled_time >= cutoff_7d]

    if len(week1_doses) >= 4 and len(week2_doses) >= 4:
        w1_taken = sum(1 for d in week1_doses if d.status == "TAKEN")
        w1_resolved = sum(1 for d in week1_doses if d.status in ["TAKEN", "MISSED"])
        w1_pct = round((w1_taken / max(1, w1_resolved)) * 100, 1)

        w2_taken = sum(1 for d in week2_doses if d.status == "TAKEN")
        w2_resolved = sum(1 for d in week2_doses if d.status in ["TAKEN", "MISSED"])
        w2_pct = round((w2_taken / max(1, w2_resolved)) * 100, 1)

        if (w1_pct - w2_pct) >= 20.0:
            existing = db.query(CareInsight).filter(
                CareInsight.profile_id == profile_id,
                CareInsight.insight_type == "ADHERENCE_DROP",
                CareInsight.created_at >= cutoff_48h
            ).first()

            if not existing:
                ai_texts = generate_ai_insight_text(
                    profile.full_name,
                    "ADHERENCE_DROP",
                    {"prev_pct": w1_pct, "curr_pct": w2_pct}
                )
                insight = CareInsight(
                    profile_id=profile_id,
                    insight_type="ADHERENCE_DROP",
                    severity="warning" if (w1_pct - w2_pct) < 35 else "urgent",
                    title_en=ai_texts["title_en"],
                    title_ta=ai_texts["title_ta"],
                    title_hi=ai_texts["title_hi"],
                    text_en=ai_texts["text_en"],
                    text_ta=ai_texts["text_ta"],
                    text_hi=ai_texts["text_hi"],
                    suggested_action=ai_texts["suggested_action_en"],
                    suggested_action_ta=ai_texts["suggested_action_ta"],
                    suggested_action_hi=ai_texts["suggested_action_hi"],
                    status="ACTIVE"
                )
                db.add(insight)
                db.commit()
                db.refresh(insight)
                created_insights.append(insight)

    # 3. Check Medicine Stock Running Out Within 3 Days
    active_meds = db.query(Medication).filter(
        Medication.profile_id == profile_id,
        Medication.is_active == True
    ).all()

    for med in active_meds:
        try:
            sched = json.loads(med.schedule_times) if med.schedule_times else ["09:00"]
            daily_count = len(sched) if isinstance(sched, list) else 1
        except Exception:
            daily_count = 1

        days_left = med.stock_count / max(1, daily_count)
        if days_left <= 3:
            existing = db.query(CareInsight).filter(
                CareInsight.profile_id == profile_id,
                CareInsight.insight_type == f"LOW_STOCK_{med.id}",
                CareInsight.created_at >= cutoff_48h
            ).first()

            if not existing:
                ai_texts = generate_ai_insight_text(
                    profile.full_name,
                    "LOW_STOCK",
                    {"med_name": med.name, "stock": med.stock_count, "days_left": round(days_left, 1)}
                )
                insight = CareInsight(
                    profile_id=profile_id,
                    insight_type=f"LOW_STOCK_{med.id}",
                    severity="urgent" if med.stock_count <= 2 else "warning",
                    title_en=ai_texts["title_en"],
                    title_ta=ai_texts["title_ta"],
                    title_hi=ai_texts["title_hi"],
                    text_en=ai_texts["text_en"],
                    text_ta=ai_texts["text_ta"],
                    text_hi=ai_texts["text_hi"],
                    suggested_action=ai_texts["suggested_action_en"],
                    suggested_action_ta=ai_texts["suggested_action_ta"],
                    suggested_action_hi=ai_texts["suggested_action_hi"],
                    status="ACTIVE"
                )
                db.add(insight)
                db.commit()
                db.refresh(insight)
                created_insights.append(insight)
            break

    # 4. Check Upcoming Appointments within 48h
    upcoming_appt = db.query(Appointment).filter(
        Appointment.profile_id == profile_id,
        Appointment.appointment_time >= now,
        Appointment.appointment_time <= now + timedelta(hours=48),
        Appointment.is_completed == False
    ).order_by(Appointment.appointment_time.asc()).first()

    if upcoming_appt:
        existing = db.query(CareInsight).filter(
            CareInsight.profile_id == profile_id,
            CareInsight.insight_type == f"APPT_{upcoming_appt.id}",
            CareInsight.created_at >= cutoff_48h
        ).first()

        if not existing:
            t_str = upcoming_appt.appointment_time.strftime("%A at %I:%M %p")
            ai_texts = generate_ai_insight_text(
                profile.full_name,
                "APPOINTMENT",
                {"doctor_name": upcoming_appt.doctor_name, "appt_time": t_str}
            )
            insight = CareInsight(
                profile_id=profile_id,
                insight_type=f"APPT_{upcoming_appt.id}",
                severity="info",
                title_en=ai_texts["title_en"],
                title_ta=ai_texts["title_ta"],
                title_hi=ai_texts["title_hi"],
                text_en=ai_texts["text_en"],
                text_ta=ai_texts["text_ta"],
                text_hi=ai_texts["text_hi"],
                suggested_action=ai_texts["suggested_action_en"],
                suggested_action_ta=ai_texts["suggested_action_ta"],
                suggested_action_hi=ai_texts["suggested_action_hi"],
                status="ACTIVE"
            )
            db.add(insight)
            db.commit()
            db.refresh(insight)
            created_insights.append(insight)

    # 5. Dispatch Email Notifications in each recipient's language
    if trigger_notifications and created_insights:
        members = db.query(ProfileMember).filter(
            ProfileMember.profile_id == profile_id,
            ProfileMember.role.in_(["CARETAKER", "FAMILY"])
        ).all()

        for ins in created_insights:
            for member in members:
                if member.email:
                    mlang = member.language or "en"
                    t_title = ins.title_hi if mlang == "hi" else (ins.title_ta if mlang == "ta" else ins.title_en)
                    t_text = ins.text_hi if mlang == "hi" else (ins.text_ta if mlang == "ta" else ins.text_en)
                    t_act = ins.suggested_action_hi if mlang == "hi" else (ins.suggested_action_ta if mlang == "ta" else ins.suggested_action)

                    send_care_insight_email(
                        recipients=[member.email],
                        elder_name=profile.full_name,
                        title=t_title,
                        text=t_text,
                        suggested_action=t_act,
                        severity=ins.severity,
                        lang=mlang
                    )

    return created_insights


def get_insights(db: Session, profile_id: str, limit: int = 20) -> List[CareInsight]:
    """
    Returns latest care insights for the profile, ordered by newest first.
    """
    return db.query(CareInsight).filter(
        CareInsight.profile_id == profile_id
    ).order_by(desc(CareInsight.created_at)).limit(limit).all()


def mark_insight_seen(db: Session, insight_id: int, profile_id: str) -> Optional[CareInsight]:
    """
    Marks an insight as SEEN.
    """
    insight = db.query(CareInsight).filter(
        CareInsight.id == insight_id,
        CareInsight.profile_id == profile_id
    ).first()
    if insight:
        insight.status = "SEEN"
        db.commit()
        db.refresh(insight)
    return insight


def run_daily_insights_job():
    """
    Background scheduler task that analyses all registered elder profiles daily.
    """
    db: Session = SessionLocal()
    try:
        profiles = db.query(Profile).all()
        for p in profiles:
            analyze_profile_insights(db, p.id, trigger_notifications=True)
    except Exception as e:
        logger.error(f"Error running daily care insights job: {e}")
    finally:
        db.close()
