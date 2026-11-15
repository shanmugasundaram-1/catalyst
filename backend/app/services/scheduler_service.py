import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Profile, ProfileMember, Medication, DoseLog, Appointment
from app.services.email_service import (
    send_upcoming_dose_email,
    send_escalation_missed_dose,
    send_appointment_reminder
)
from app.services.insights_service import run_daily_insights_job

logger = logging.getLogger("ayucare.scheduler")
scheduler = BackgroundScheduler()

def check_upcoming_and_missed_doses():
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        
        # 1. Check for upcoming doses in 10 minutes (between +8m and +12m)
        window_start = now + timedelta(minutes=8)
        window_end = now + timedelta(minutes=12)

        upcoming_doses = db.query(DoseLog).filter(
            DoseLog.status == "PENDING",
            DoseLog.scheduled_time >= window_start,
            DoseLog.scheduled_time <= window_end
        ).all()

        for dose in upcoming_doses:
            med = dose.medication
            profile = dose.profile
            if not med or not profile:
                continue

            # Find elder member email
            elder_member = db.query(ProfileMember).filter(
                ProfileMember.profile_id == profile.id,
                ProfileMember.role == "ELDER"
            ).first()

            elder_email = elder_member.email if elder_member else None
            elder_lang = elder_member.language if (elder_member and elder_member.language) else (profile.language or "en")
            if elder_email:
                time_str = dose.scheduled_time.strftime("%I:%M %p")
                send_upcoming_dose_email(
                    elder_email=elder_email,
                    elder_name=profile.full_name,
                    med_name=med.name,
                    dosage=med.dosage,
                    scheduled_time_str=time_str,
                    food_timing=med.food_timing,
                    lang=elder_lang
                )

        # 2. Check for overdue doses and escalate
        # Threshold 1: 15 mins past due -> Mark MISSED and Escalate Level 1 (Elder)
        overdue_15m = now - timedelta(minutes=15)
        # Threshold 2: 30 mins past due -> Escalate Level 2 (Caretaker)
        overdue_30m = now - timedelta(minutes=30)
        # Threshold 3: 45 mins past due -> Escalate Level 3 (Family)
        overdue_45m = now - timedelta(minutes=45)

        # Fetch unresolved doses past 15 mins
        escalation_candidates = db.query(DoseLog).filter(
            DoseLog.status.in_(["PENDING", "MISSED"]),
            DoseLog.scheduled_time <= overdue_15m,
            DoseLog.escalation_level < 3
        ).all()

        for dose in escalation_candidates:
            med = dose.medication
            profile = dose.profile
            if not med or not profile:
                continue

            time_str = dose.scheduled_time.strftime("%I:%M %p")
            scheduled_t = dose.scheduled_time

            # LEVEL 1: Immediately after 15m past due
            if dose.escalation_level == 0:
                dose.status = "MISSED"
                dose.escalation_level = 1
                db.commit()

                elder_members = db.query(ProfileMember).filter(
                    ProfileMember.profile_id == profile.id,
                    ProfileMember.role == "ELDER"
                ).all()
                for m in elder_members:
                    if m.email:
                        send_escalation_missed_dose(1, [m.email], profile.full_name, med.name, med.dosage, time_str, lang=m.language or "en")

            # LEVEL 2: 30m past due
            elif dose.escalation_level == 1 and scheduled_t <= overdue_30m:
                dose.escalation_level = 2
                db.commit()

                caretakers = db.query(ProfileMember).filter(
                    ProfileMember.profile_id == profile.id,
                    ProfileMember.role == "CARETAKER"
                ).all()
                for m in caretakers:
                    if m.email:
                        send_escalation_missed_dose(2, [m.email], profile.full_name, med.name, med.dosage, time_str, lang=m.language or "en")

            # LEVEL 3: 45m past due
            elif dose.escalation_level == 2 and scheduled_t <= overdue_45m:
                dose.escalation_level = 3
                db.commit()

                family_members = db.query(ProfileMember).filter(
                    ProfileMember.profile_id == profile.id,
                    ProfileMember.role == "FAMILY"
                ).all()
                for m in family_members:
                    if m.email:
                        send_escalation_missed_dose(3, [m.email], profile.full_name, med.name, med.dosage, time_str, lang=m.language or "en")

    except Exception as e:
        logger.error(f"Error in dose scheduler job: {e}")
    finally:
        db.close()


def check_appointment_reminders():
    db: Session = SessionLocal()
    try:
        now = datetime.now()

        # 24-hour reminder
        appts_24h = db.query(Appointment).filter(
            Appointment.is_completed == False,
            Appointment.reminder_sent_24h == False,
            Appointment.appointment_time >= now,
            Appointment.appointment_time <= now + timedelta(hours=25),
            Appointment.appointment_time >= now + timedelta(hours=23)
        ).all()

        for appt in appts_24h:
            members = db.query(ProfileMember).filter(ProfileMember.profile_id == appt.profile_id).all()
            for m in members:
                if m.email:
                    send_appointment_reminder(
                        recipients=[m.email],
                        elder_name=appt.profile.full_name,
                        doctor=appt.doctor_name,
                        specialty=appt.specialty,
                        appt_time_str=appt.appointment_time.strftime("%B %d, %Y at %I:%M %p"),
                        location=appt.location,
                        notes=appt.notes,
                        lang=m.language or "en"
                    )
            appt.reminder_sent_24h = True
            db.commit()

        # 2-hour reminder
        appts_2h = db.query(Appointment).filter(
            Appointment.is_completed == False,
            Appointment.reminder_sent_2h == False,
            Appointment.appointment_time >= now,
            Appointment.appointment_time <= now + timedelta(hours=2, minutes=30),
            Appointment.appointment_time >= now + timedelta(hours=1, minutes=30)
        ).all()

        for appt in appts_2h:
            members = db.query(ProfileMember).filter(ProfileMember.profile_id == appt.profile_id).all()
            for m in members:
                if m.email:
                    send_appointment_reminder(
                        recipients=[m.email],
                        elder_name=appt.profile.full_name,
                        doctor=appt.doctor_name,
                        specialty=appt.specialty,
                        appt_time_str=appt.appointment_time.strftime("%I:%M %p Today"),
                        location=appt.location,
                        notes=appt.notes,
                        lang=m.language or "en"
                    )
            appt.reminder_sent_2h = True
            db.commit()

    except Exception as e:
        logger.error(f"Error in appointment scheduler job: {e}")
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_upcoming_and_missed_doses, "interval", minutes=1, id="dose_check", replace_existing=True)
        scheduler.add_job(check_appointment_reminders, "interval", minutes=5, id="appt_check", replace_existing=True)
        scheduler.add_job(run_daily_insights_job, "interval", hours=24, id="daily_insights", replace_existing=True)
        scheduler.start()
        logger.info("APScheduler background service started successfully.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped.")
