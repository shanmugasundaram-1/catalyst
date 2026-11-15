import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional, Union, Tuple, Dict
from app.core.config import settings

logger = logging.getLogger("ayucare.email")

# In-memory sent email audit for hackathon live demo inspector
sent_email_history: List[dict] = []

def send_html_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    plain_fallback: Optional[str] = None,
    language: str = "en"
) -> bool:
    if not to_emails:
        logger.warning("send_html_email called with empty recipient list.")
        return False

    valid_recipients = [e.strip() for e in to_emails if e and "@" in e]
    if not valid_recipients:
        return False

    record = {
        "timestamp": datetime.now().isoformat(),
        "to": valid_recipients,
        "subject": subject,
        "language": language,
        "preview": plain_fallback or subject,
        "html": html_content
    }
    sent_email_history.insert(0, record)
    if len(sent_email_history) > 100:
        sent_email_history.pop()

    if settings.SMTP_MOCK or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"📧 [MOCK EMAIL DISPATCHED ({language.upper()})] To: {valid_recipients} | Subject: '{subject}'")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = ", ".join(valid_recipients)

        if plain_fallback:
            part1 = MIMEText(plain_fallback, "plain", "utf-8")
            msg.attach(part1)

        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part2)

        if settings.SMTP_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_TLS:
                server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL or settings.SMTP_USER, valid_recipients, msg.as_string())
        server.quit()
        logger.info(f"✅ Real email ({language.upper()}) sent to {valid_recipients}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send SMTP email: {e}")
        return False


def get_base_template(title: str, body_html: str, alert_type: str = "info", lang: str = "en") -> str:
    color_map = {
        "danger": "#DC2626",
        "warning": "#D97706",
        "info": "#2563EB",
        "success": "#16A34A"
    }
    header_color = color_map.get(alert_type, "#2563EB")

    footer_texts = {
        "en": (
            "AyuCare • Keeping Our Elders at the Center of Care • Google Build with AI",
            "Need urgent help? Call emergency services or the elder's designated caretaker."
        ),
        "ta": (
            "ஆயு கேர் • முதியோரின் நலன் மற்றும் உரிமையை முன்னிறுத்தும் தளம் • Google Build with AI",
            "அவசர உதவி தேவையா? உடனடியாக அவசர சேவைகள் அல்லது நியமிக்கப்பட்ட பராமரிப்பாளரை அழைக்கவும்."
        ),
        "hi": (
            "आयु केयर • बुजुर्गों की देखभाल और निर्णय अधिकार को प्राथमिकता • Google Build with AI",
            "तत्काल सहायता चाहिए? आपातकालीन सेवाओं या बुजुर्ग के निर्धारित देखभालकर्ता को तुरंत कॉल करें।"
        )
    }
    f1, f2 = footer_texts.get(lang, footer_texts["en"])

    font_family = (
        "'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        if lang == "hi"
        else "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
      <meta charset="utf-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap" rel="stylesheet">
      <style>
        body {{ font-family: {font_family}; background-color: #F8FAFC; margin: 0; padding: 20px; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .header {{ background-color: {header_color}; color: #FFFFFF; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
        .content {{ padding: 28px 24px; color: #1E293B; line-height: 1.6; font-size: 16px; }}
        .footer {{ background-color: #F1F5F9; padding: 16px; text-align: center; font-size: 12px; color: #64748B; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>{title}</h1>
        </div>
        <div class="content">
          {body_html}
        </div>
        <div class="footer">
          <p>{f1}</p>
          <p>{f2}</p>
        </div>
      </div>
    </body>
    </html>
    """


# Helper for food timing translation in emails
def format_food_timing(food_timing: str, lang: str = "en") -> str:
    mapping = {
        "AFTER_FOOD": {"en": "After Food", "ta": "சாப்பிட்ட பிறகு", "hi": "खाने के बाद"},
        "BEFORE_FOOD": {"en": "Before Food", "ta": "சாப்பிடுவதற்கு முன்", "hi": "खाने से पहले"},
        "WITH_FOOD": {"en": "With Food", "ta": "உணவுடன்", "hi": "भोजन के साथ"},
        "ANYTIME": {"en": "Anytime", "ta": "எப்போதும்", "hi": "कभी भी"}
    }
    return mapping.get(food_timing, {}).get(lang, food_timing.replace("_", " ").title())


def send_upcoming_dose_email(
    elder_email: str,
    elder_name: str,
    med_name: str,
    dosage: str,
    scheduled_time_str: str,
    food_timing: str,
    lang: str = "en"
):
    food_str = format_food_timing(food_timing, lang)
    if lang == "hi":
        subject = f"दवा अनुस्मारक: {med_name} समय {scheduled_time_str}"
        title = "⏰ दवा अनुस्मारक (अगले 10 मिनट में)"
        body = f"""
        <p>आदरणीय <strong>{elder_name}</strong>,</p>
        <p>आपकी दवा लेने का समय हो गया है:</p>
        <div style="background:#EFF6FF; border-left: 4px solid #2563EB; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #1E40AF; font-size: 20px;">{med_name} ({dosage})</h3>
          <p style="margin: 4px 0;"><strong>निर्धारित समय:</strong> {scheduled_time_str}</p>
          <p style="margin: 4px 0;"><strong>भोजन निर्देश:</strong> {food_str}</p>
        </div>
        <p>कृपया दवा पानी के साथ लें और लेने के बाद अपने AyuCare स्क्रीन पर <strong>"मैंने दवा ले ली"</strong> बटन अवश्य दबाएं।</p>
        """
    elif lang == "ta":
        subject = f"மருந்து நினைவூட்டல்: {med_name} - {scheduled_time_str}"
        title = "⏰ மருந்து நினைவூட்டல் (அடுத்த 10 நிமிடங்களில்)"
        body = f"""
        <p>அன்புடையீர் <strong>{elder_name}</strong>,</p>
        <p>உங்கள் மருந்தை உட்கொள்ளும் நேரம் நெருங்கிவிட்டது:</p>
        <div style="background:#EFF6FF; border-left: 4px solid #2563EB; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #1E40AF; font-size: 20px;">{med_name} ({dosage})</h3>
          <p style="margin: 4px 0;"><strong>குறிக்கப்பட்ட நேரம்:</strong> {scheduled_time_str}</p>
          <p style="margin: 4px 0;"><strong>உணவு முறை:</strong> {food_str}</p>
        </div>
        <p>தயவுசெய்து மருந்தை தண்ணீருடன் உட்கொண்டு AyuCare செயலியில் பதிவு செய்யவும்.</p>
        """
    else:
        subject = f"Medication Reminder: {med_name} at {scheduled_time_str}"
        title = "⏰ Medication Reminder (Next 10 Minutes)"
        body = f"""
        <p>Dear <strong>{elder_name}</strong>,</p>
        <p>It's almost time for your medication:</p>
        <div style="background:#EFF6FF; border-left: 4px solid #2563EB; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #1E40AF; font-size: 20px;">{med_name} ({dosage})</h3>
          <p style="margin: 4px 0;"><strong>Scheduled Time:</strong> {scheduled_time_str}</p>
          <p style="margin: 4px 0;"><strong>Food Instruction:</strong> {food_str}</p>
        </div>
        <p>Please take your dose with water and remember to mark it as taken in your AyuCare screen.</p>
        """

    html = get_base_template(title, body, alert_type="info", lang=lang)
    send_html_email([elder_email], subject, html, f"Time to take {med_name} {dosage} at {scheduled_time_str}", language=lang)


def send_escalation_missed_dose(
    level: int,
    recipients: List[str],
    elder_name: str,
    med_name: str,
    dosage: str,
    scheduled_time_str: str,
    lang: str = "en"
):
    """
    Sends escalation notification in recipient's specified language ('en', 'ta', or 'hi').
    """
    if level == 1:
        # Immediate alert to Elder
        if lang == "hi":
            subject = f"छूटी हुई खुराक जाँच: {med_name}"
            title = "⚠️ छूटी हुई खुराक जाँच"
            body = f"""
            <p>आदरणीय <strong>{elder_name}</strong>,</p>
            <p>आपकी दवा <strong>{med_name} ({dosage})</strong> का निर्धारित समय <strong>{scheduled_time_str}</strong> था, जो अभी तक दर्ज नहीं हुई है।</p>
            <p>यदि आपने दवा ले ली है, तो कृपया ऐप में <strong>"मैंने दवा ले ली"</strong> बटन दबाएं। यदि आप अस्वस्थ महसूस कर रहे हैं, तो तुरंत अपने देखभालकर्ता से संपर्क करें।</p>
            """
        elif lang == "ta":
            subject = f"தவறிய மருந்து சரிபார்ப்பு: {med_name}"
            title = "⚠️ தவறவிட்ட மருந்து சரிபார்ப்பு"
            body = f"""
            <p>அன்புடையீர் <strong>{elder_name}</strong>,</p>
            <p>உங்களுக்கு <strong>{scheduled_time_str}</strong> மணிக்கு திட்டமிடப்பட்ட <strong>{med_name} ({dosage})</strong> மருந்து இன்னும் எடுக்கப்படவில்லை எனத் தெரிகிறது.</p>
            <p>ஏற்கனவே எடுத்துவிட்டீர்கள் எனில் <strong>"சாப்பிட்டுவிட்டேன்"</strong> என குறிக்கவும். உதவி தேவைப்பட்டால் பராமரிப்பாளரை தொடர்பு கொள்ளவும்.</p>
            """
        else:
            subject = f"Missed Dose Check-in: {med_name}"
            title = "⚠️ Missed Dose Check-in"
            body = f"""
            <p>Dear <strong>{elder_name}</strong>,</p>
            <p>You had a dose of <strong>{med_name} ({dosage})</strong> scheduled for <strong>{scheduled_time_str}</strong> that hasn't been recorded yet.</p>
            <p>If you already took it, please tap <strong>"I took it"</strong> in your AyuCare app. If you need help or feel unwell, please contact your caretaker.</p>
            """
        html = get_base_template(title, body, alert_type="warning", lang=lang)
        send_html_email(recipients, subject, html, language=lang)

    elif level == 2:
        # Caretaker escalation (15 min)
        if lang == "hi":
            subject = f"देखभालकर्ता सतर्कता: {elder_name} ने खुराक {med_name} नहीं ली"
            title = "🚨 देखभालकर्ता सतर्कता: छूटी हुई दवा"
            body = f"""
            <p>देखभालकर्ता ध्यान दें,</p>
            <p>बुजुर्ग <strong>{elder_name}</strong> ने अपनी निर्धारित दवा अभी तक नहीं ली है:</p>
            <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
              <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{med_name} ({dosage})</h3>
              <p style="margin: 4px 0;"><strong>निर्धारित समय:</strong> {scheduled_time_str}</p>
              <p style="margin: 4px 0;"><strong>स्थिति:</strong> 15 मिनट से अधिक समय से अपुष्ट</p>
            </div>
            <p>कृपया {elder_name} का हालचाल लें और सुनिश्चित करें कि वे स्वस्थ हैं।</p>
            """
        elif lang == "ta":
            subject = f"பராமரிப்பாளர் எச்சரிக்கை: {elder_name} மருந்து {med_name} எடுக்கவில்லை"
            title = "🚨 பராமரிப்பாளர் எச்சரிக்கை: தவறிய மருந்து"
            body = f"""
            <p>பராமரிப்பாளர் கவனத்திற்கு,</p>
            <p>முதியவர் <strong>{elder_name}</strong> தனது அட்டவணைப்படுத்தப்பட்ட மருந்தை இன்னும் எடுக்கவில்லை:</p>
            <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
              <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{med_name} ({dosage})</h3>
              <p style="margin: 4px 0;"><strong>நேரம்:</strong> {scheduled_time_str}</p>
              <p style="margin: 4px 0;"><strong>நிலை:</strong> 15 நிமிடங்களுக்கு மேலாக உறுதிப்படுத்தப்படவில்லை</p>
            </div>
            <p>தயவுசெய்து {elder_name} அவர்களிடம் பேசி உதவி செய்யவும்.</p>
            """
        else:
            subject = f"CARETAKER ALERT: {elder_name} missed {med_name}"
            title = "🚨 Caretaker Alert: Missed Medication"
            body = f"""
            <p>Attention Caretaker,</p>
            <p>Elder <strong>{elder_name}</strong> has not recorded their scheduled medication:</p>
            <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
              <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{med_name} ({dosage})</h3>
              <p style="margin: 4px 0;"><strong>Scheduled For:</strong> {scheduled_time_str}</p>
              <p style="margin: 4px 0;"><strong>Status:</strong> Unconfirmed for over 15 minutes</p>
            </div>
            <p>Please check in on {elder_name} to ensure they are well and assist them if needed.</p>
            """
        html = get_base_template(title, body, alert_type="warning", lang=lang)
        send_html_email(recipients, subject, html, language=lang)

    elif level == 3:
        # Family escalation (30-45 min)
        if lang == "hi":
            subject = f"परिवार सूचना: {elder_name} ने खुराक {med_name} नहीं ली"
            title = "🚨 परिवार सूचना: दवा लंबित सतर्कता"
            body = f"""
            <p>प्रिय परिवारजनों,</p>
            <p>यह <strong>{elder_name}</strong> के स्वास्थ्य और दवा के संबंध में एक महत्वपूर्ण सूचना है।</p>
            <p>समय <strong>{scheduled_time_str}</strong> पर निर्धारित <strong>{med_name} ({dosage})</strong> अभी तक दर्ज नहीं हुई है (30+ मिनट से लंबित)।</p>
            <p>प्राथमिक देखभालकर्ता को पहले ही सूचित किया जा चुका है। यह सूचना परिवार की जानकारी के लिए भेजी गई है।</p>
            """
        elif lang == "ta":
            subject = f"குடும்பத்தினர் அறிவிப்பு: {elder_name} மருந்து {med_name} எடுக்கவில்லை"
            title = "🚨 குடும்பத்தினர் அறிவிப்பு: மருந்து நிலுவை எச்சரிக்கை"
            body = f"""
            <p>அன்பான குடும்பத்தினரே,</p>
            <p>இது <strong>{elder_name}</strong> அவர்களின் மருந்து உட்கொள்ளல் குறித்த முக்கிய அறிவிப்பு.</p>
            <p><strong>{scheduled_time_str}</strong> மணிக்கு திட்டமிடப்பட்ட <strong>{med_name} ({dosage})</strong> இன்னும் எடுக்கப்படவில்லை (30+ நிமிடங்களுக்கு மேல் நிலுவை).</p>
            <p>முதன்மை பராமரிப்பாளருக்கு ஏற்கனவே தகவல் தெரிவிக்கப்பட்டுள்ளது. குடும்பத்தின் கவனத்திற்கு இது அனுப்பப்படுகிறது.</p>
            """
        else:
            subject = f"FAMILY NOTICE: {elder_name} missed dose {med_name}"
            title = "🚨 Family Notice: Medication Pending Check"
            body = f"""
            <p>Dear Family Members,</p>
            <p>This is a care notification regarding <strong>{elder_name}</strong>.</p>
            <p>The dose of <strong>{med_name} ({dosage})</strong> scheduled at <strong>{scheduled_time_str}</strong> has not yet been marked taken (30+ minutes past due).</p>
            <p>The primary caretaker has already been alerted. This notice is sent to ensure family visibility.</p>
            """
        html = get_base_template(title, body, alert_type="danger", lang=lang)
        send_html_email(recipients, subject, html, language=lang)


def send_appointment_reminder(
    recipients: List[str],
    elder_name: str,
    doctor: str,
    specialty: str,
    appt_time_str: str,
    location: str,
    notes: str,
    lang: str = "en"
):
    if lang == "hi":
        subject = f"डॉक्टर अपॉइंटमेंट अनुस्मारक: डॉ. {doctor} ({appt_time_str})"
        title = "🩺 आगामी डॉक्टर अपॉइंटमेंट"
        body = f"""
        <p>प्रिय <strong>{elder_name}</strong> का देखभाल मंडल,</p>
        <p>यह आगामी चिकित्सकीय परामर्श के लिए अनुस्मारक है:</p>
        <div style="background:#F0FDF4; border-left: 4px solid #16A34A; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #166534; font-size: 18px;">डॉ. {doctor} ({specialty})</h3>
          <p style="margin: 4px 0;"><strong>कब:</strong> {appt_time_str}</p>
          <p style="margin: 4px 0;"><strong>कहाँ:</strong> {location}</p>
          {f'<p style="margin: 4px 0;"><strong>विशेष नोट:</strong> {notes}</p>' if notes else ''}
        </div>
        <p>कृपया आवश्यक यात्रा या साथी की व्यवस्था समय पर करें।</p>
        """
    elif lang == "ta":
        subject = f"மருத்துவ சந்திப்பு நினைவூட்டல்: டாக்டர் {doctor} ({appt_time_str})"
        title = "🩺 திட்டமிடப்பட்ட மருத்துவ சந்திப்பு"
        body = f"""
        <p>அன்புடையீர் <strong>{elder_name}</strong> பராமரிப்புக் குழு,</p>
        <p>வரவிருக்கும் மருத்துவ ஆலோசனையின் நினைவூட்டல்:</p>
        <div style="background:#F0FDF4; border-left: 4px solid #16A34A; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #166534; font-size: 18px;">டாக்டர் {doctor} ({specialty})</h3>
          <p style="margin: 4px 0;"><strong>எப்போது:</strong> {appt_time_str}</p>
          <p style="margin: 4px 0;"><strong>இடம்:</strong> {location}</p>
          {f'<p style="margin: 4px 0;"><strong>குறிப்புகள்:</strong> {notes}</p>' if notes else ''}
        </div>
        <p>பயண மற்றும் துணை ஏற்பாடுகளை முன்கூட்டியே செய்து கொள்ளவும்.</p>
        """
    else:
        subject = f"Appointment Reminder: Dr. {doctor} on {appt_time_str}"
        title = "🩺 Upcoming Medical Appointment"
        body = f"""
        <p>Dear Care Circle of <strong>{elder_name}</strong>,</p>
        <p>This is a reminder for an upcoming medical consultation:</p>
        <div style="background:#F0FDF4; border-left: 4px solid #16A34A; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #166534; font-size: 18px;">Dr. {doctor} ({specialty})</h3>
          <p style="margin: 4px 0;"><strong>When:</strong> {appt_time_str}</p>
          <p style="margin: 4px 0;"><strong>Where:</strong> {location}</p>
          {f'<p style="margin: 4px 0;"><strong>Notes:</strong> {notes}</p>' if notes else ''}
        </div>
        <p>Please make necessary travel or companion arrangements.</p>
        """

    html = get_base_template(title, body, alert_type="success", lang=lang)
    send_html_email(recipients, subject, html, language=lang)


def send_sos_alert(
    recipients: List[str],
    elder_name: str,
    timestamp_str: str,
    emergency_phone: str,
    notes: str,
    lang: str = "en"
):
    if lang == "hi":
        subject = f"अति आवश्यक: {elder_name} की तरफ से आपातकालीन SOS अलर्ट!"
        title = "🚨 आपातकालीन SOS सक्रिय किया गया!"
        body = f"""
        <div style="background:#FEF2F2; border: 2px solid #DC2626; padding: 18px; border-radius: 8px; text-align: center;">
          <h2 style="color: #991B1B; margin: 0 0 8px 0;">आपातकालीन अलर्ट (EMERGENCY)</h2>
          <p style="font-size: 18px; margin: 0; color: #7F1D1D;">
            <strong>{elder_name}</strong> ने आपातकालीन SOS बटन दबाया है!
          </p>
        </div>
        <p style="margin-top: 20px;"><strong>समय:</strong> {timestamp_str}</p>
        <p><strong>प्राथमिक फोन:</strong> <a href="tel:{emergency_phone}">{emergency_phone or 'उपलब्ध नहीं'}</a></p>
        <p><strong>आपातकालीन मेडिकल नोट्स:</strong> {notes or 'कोई विशेष नोट नहीं'}</p>
        <p style="color: #DC2626; font-weight: bold; font-size: 16px;">
          कृपया बुजुर्ग को तुरंत कॉल करें या उनकी सुरक्षा सुनिश्चित करने के लिए तुरंत उनके स्थान पर जाएँ!
        </p>
        """
    elif lang == "ta":
        subject = f"அவசரம்: {elder_name}-இடமிருந்து அவசர SOS எச்சரிக்கை!"
        title = "🚨 அவசர உதவி (SOS) கோரப்பட்டுள்ளது!"
        body = f"""
        <div style="background:#FEF2F2; border: 2px solid #DC2626; padding: 18px; border-radius: 8px; text-align: center;">
          <h2 style="color: #991B1B; margin: 0 0 8px 0;">அவசர எச்சரிக்கை</h2>
          <p style="font-size: 18px; margin: 0; color: #7F1D1D;">
            <strong>{elder_name}</strong> அவசர SOS பொத்தானை அழுத்தியுள்ளார்!
          </p>
        </div>
        <p style="margin-top: 20px;"><strong>நேரம்:</strong> {timestamp_str}</p>
        <p><strong>முதன்மை தொலைபேசி:</strong> <a href="tel:{emergency_phone}">{emergency_phone or 'வழங்கப்படவில்லை'}</a></p>
        <p><strong>மருத்துவக் குறிப்புகள்:</strong> {notes or 'குறிப்புகள் இல்லை'}</p>
        <p style="color: #DC2626; font-weight: bold; font-size: 16px;">
          தயவுசெய்து முதியவரை உடனே அழைக்கவும் அல்லது நேரில் சென்று பாதுகாப்பை உறுதி செய்யவும்!
        </p>
        """
    else:
        subject = f"URGENT: SOS Alert from {elder_name}!"
        title = "🚨 EMERGENCY SOS TRIGGERED!"
        body = f"""
        <div style="background:#FEF2F2; border: 2px solid #DC2626; padding: 18px; border-radius: 8px; text-align: center;">
          <h2 style="color: #991B1B; margin: 0 0 8px 0;">EMERGENCY ALERT</h2>
          <p style="font-size: 18px; margin: 0; color: #7F1D1D;">
            <strong>{elder_name}</strong> pressed the Emergency SOS button!
          </p>
        </div>
        <p style="margin-top: 20px;"><strong>Time:</strong> {timestamp_str}</p>
        <p><strong>Primary Phone:</strong> <a href="tel:{emergency_phone}">{emergency_phone or 'Not provided'}</a></p>
        <p><strong>Emergency Medical Notes:</strong> {notes or 'None listed'}</p>
        <p style="color: #DC2626; font-weight: bold; font-size: 16px;">
          Please call the elder immediately or visit their location to verify safety!
        </p>
        """

    html = get_base_template(title, body, alert_type="danger", lang=lang)
    send_html_email(recipients, subject, html, language=lang)


def send_weekly_summary_email(
    recipients: List[str],
    elder_name: str,
    adherence_pct: float,
    summary_text_en: str,
    summary_text_ta: str,
    summary_text_hi: str,
    upcoming_appts: List[str],
    lang: str = "en"
):
    appts_html = "".join([f"<li>{a}</li>" for a in upcoming_appts]) if upcoming_appts else "<li>No appointments scheduled</li>"

    if lang == "hi":
        title = f"📊 साप्ताहिक स्वास्थ्य व दवा रिपोर्ट: {elder_name}"
        subject = f"साप्ताहिक देखभाल सारांश: {elder_name} ({adherence_pct}% नियमितता)"
        body = f"""
        <p>प्रिय परिवार व देखभाल दल,</p>
        <p>यहाँ <strong>{elder_name}</strong> के लिए इस सप्ताह का AI-सक्षम स्वास्थ्य सारांश है:</p>
        <div style="background:#F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin:0 0 8px 0; color:#0F172A;">साप्ताहिक नियमितता (Adherence): <span style="color:#16A34A;">{adherence_pct}%</span></h3>
          <p style="margin:8px 0;"><strong>हिन्दी सारांश:</strong></p>
          <p style="font-style: italic; color:#334155; font-size: 17px;">"{summary_text_hi}"</p>
          <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 12px 0;">
          <p style="margin:8px 0; font-size: 13px; color:#64748B;"><strong>English Version:</strong> "{summary_text_en}"</p>
        </div>
        <h4>आगामी डॉक्टर अपॉइंटमेंट्स:</h4>
        <ul>{appts_html}</ul>
        """
    elif lang == "ta":
        title = f"📊 வாராந்திர நலன் & மருந்து அறிக்கை: {elder_name}"
        subject = f"வாராந்திர பராமரிப்பு சுருக்கம்: {elder_name} ({adherence_pct}% வெற்றி)"
        body = f"""
        <p>அன்பான குடும்பத்தினரே,</p>
        <p><strong>{elder_name}</strong> அவர்களின் இந்த வார AI-உதவி நலன் அறிக்கை:</p>
        <div style="background:#F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin:0 0 8px 0; color:#0F172A;">வாராந்திர மருந்து உட்கொள்ளல்: <span style="color:#16A34A;">{adherence_pct}%</span></h3>
          <p style="margin:8px 0;"><strong>தமிழ் வடிவம்:</strong></p>
          <p style="font-style: italic; color:#334155; font-size: 17px;">"{summary_text_ta}"</p>
          <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 12px 0;">
          <p style="margin:8px 0; font-size: 13px; color:#64748B;"><strong>English Version:</strong> "{summary_text_en}"</p>
        </div>
        <h4>வரவிருக்கும் மருத்துவ சந்திப்புகள்:</h4>
        <ul>{appts_html}</ul>
        """
    else:
        title = f"📊 Weekly Health & Medication Summary: {elder_name}"
        subject = f"Weekly Care Summary for {elder_name} ({adherence_pct}% Adherence)"
        body = f"""
        <p>Dear Family & Care Team,</p>
        <p>Here is this week's AI-assisted care summary for <strong>{elder_name}</strong>:</p>
        <div style="background:#F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 8px; margin: 16px 0;">
          <h3 style="margin:0 0 8px 0; color:#0F172A;">Weekly Adherence: <span style="color:#16A34A;">{adherence_pct}%</span></h3>
          <p style="margin:8px 0;"><strong>Summary:</strong></p>
          <p style="font-style: italic; color:#334155;">"{summary_text_en}"</p>
          <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 12px 0;">
          <p style="margin:8px 0; font-size: 13px; color:#64748B;"><strong>हिन्दी:</strong> "{summary_text_hi}"</p>
          <p style="margin:8px 0; font-size: 13px; color:#64748B;"><strong>தமிழ்:</strong> "{summary_text_ta}"</p>
        </div>
        <h4>Upcoming Appointments:</h4>
        <ul>{appts_html}</ul>
        """

    html = get_base_template(title, body, alert_type="info", lang=lang)
    send_html_email(recipients, subject, html, language=lang)


def send_care_insight_email(
    recipients: List[str],
    elder_name: str,
    title: str,
    text: str,
    suggested_action: str,
    severity: str = "warning",
    lang: str = "en"
):
    """
    Sends AI Early Warning & Care Insight email to caretaker/family in recipient's language.
    """
    alert_type = "danger" if severity == "urgent" else ("warning" if severity == "warning" else "info")

    if lang == "hi":
        subj = f"स्वास्थ्य अंतर्दृष्टि अलर्ट ({elder_name}): {title}"
        header_title = f"💡 देखभाल अंतर्दृष्टि ({elder_name})"
        body = f"""
        <p>प्रिय देखभाल दल व परिवारजनों,</p>
        <p>AyuCare AI ने <strong>{elder_name}</strong> के हालिया 14 दिनों के दवा डेटा में निम्नलिखित महत्वपूर्ण पैटर्न देखा है:</p>
        <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{title}</h3>
          <p style="margin: 6px 0; font-size: 16px; color: #1E293B;">{text}</p>
          <hr style="border: 0; border-top: 1px solid #FED7AA; margin: 12px 0;">
          <p style="margin: 4px 0; font-weight: bold; color: #9A3412;">सुझाया गया कदम: {suggested_action}</p>
        </div>
        <p style="font-size: 13px; color: #64748B; font-style: italic;">
          * यह चिकित्सकीय सलाह नहीं है। दवा कार्यक्रम या खुराक बदलने से पहले कृपया अपने डॉक्टर से परामर्श लें।
        </p>
        """
    elif lang == "ta":
        subj = f"நலன் முன்னெச்சரிக்கை அறிக்கை ({elder_name}): {title}"
        header_title = f"💡 பராமரிப்பு நுண்ணறிவு ({elder_name})"
        body = f"""
        <p>அன்பான பராமரிப்பாளர் மற்றும் குடும்பத்தினரே,</p>
        <p>AyuCare AI <strong>{elder_name}</strong> அவர்களின் கடந்த 14 நாட்கள் மருந்து உட்கொள்ளலில் பின்வரும் முக்கிய அம்சத்தை கண்டறிந்துள்ளது:</p>
        <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{title}</h3>
          <p style="margin: 6px 0; font-size: 16px; color: #1E293B;">{text}</p>
          <hr style="border: 0; border-top: 1px solid #FED7AA; margin: 12px 0;">
          <p style="margin: 4px 0; font-weight: bold; color: #9A3412;">பரிந்துரைக்கப்பட்ட நடவடிக்கை: {suggested_action}</p>
        </div>
        <p style="font-size: 13px; color: #64748B; font-style: italic;">
          * இது மருத்துவ ஆலோசனை அல்ல. மருந்துகளில் மாற்றம் செய்வதற்கு முன் உங்கள் மருத்துவரிடம் ஆலோசனை பெறவும்.
        </p>
        """
    else:
        subj = f"Care Insight Alert ({elder_name}): {title}"
        header_title = f"💡 Care Insight & Early Warning ({elder_name})"
        body = f"""
        <p>Dear Care Circle & Family,</p>
        <p>AyuCare AI detected the following health observation from <strong>{elder_name}'s</strong> recent 14-day medication logs:</p>
        <div style="background:#FFFBEB; border-left: 4px solid #D97706; padding: 16px; margin: 20px 0; border-radius: 8px;">
          <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 18px;">{title}</h3>
          <p style="margin: 6px 0; font-size: 16px; color: #1E293B;">{text}</p>
          <hr style="border: 0; border-top: 1px solid #FED7AA; margin: 12px 0;">
          <p style="margin: 4px 0; font-weight: bold; color: #9A3412;">Suggested Action: {suggested_action}</p>
        </div>
        <p style="font-size: 13px; color: #64748B; font-style: italic;">
          * This AI insight is for guidance and awareness only. Please consult your prescribing physician before altering any medication regimen.
        </p>
        """

    html = get_base_template(header_title, body, alert_type=alert_type, lang=lang)
    send_html_email(recipients, subj, html, plain_fallback=f"{title}: {text}. Action: {suggested_action}", language=lang)
