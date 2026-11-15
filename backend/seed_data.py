import json
from datetime import datetime, date, time, timedelta, timezone
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_passcode
from app.models import (
    Profile,
    ProfileMember,
    Medication,
    DoseLog,
    Appointment,
    PendingChange,
    ActivityLog,
    CareInsight
)
from app.services.insights_service import analyze_profile_insights

def seed():
    print("🌱 Initializing database and seeding demo data...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        profile_id = "DEMO-ELDER"

        # 1. Create Elder Profile
        demo_profile = Profile(
            id=profile_id,
            full_name="Broly",
            age=74,
            blood_group="B+",
            emergency_phone="+91 98401 23456",
            emergency_notes="Type 2 Diabetes, mild hypertension. Allergic to Penicillin. Spare key with flat 302.",
            elder_passcode_hash=hash_passcode("1111"),
            caretaker_passcode_hash=hash_passcode("2222"),
            family_passcode_hash=hash_passcode("3333"),
            auto_approve_caretaker=False,
            language="ta"
        )
        db.add(demo_profile)
        db.commit()

        # 2. Add Members with multilingual preferences: Elder (ta), Caretaker (en), Family (hi)
        members = [
            ProfileMember(
                profile_id=profile_id,
                role="ELDER",
                name="Broly",
                email="broly@ayucare.demo",
                phone="+91 98401 23456",
                language="ta"
            ),
            ProfileMember(
                profile_id=profile_id,
                role="CARETAKER",
                name="Priya (Care Nurse)",
                email="priya.care@ayucare.demo",
                phone="+91 98765 43210",
                language="en"
            ),
            ProfileMember(
                profile_id=profile_id,
                role="FAMILY",
                name="Karthik (Son)",
                email="karthik.family@ayucare.demo",
                phone="+65 9123 4567",
                language="hi"
            )
        ]
        db.add_all(members)
        db.commit()

        # 3. Add Medications
        today = date.today()
        medications = [
            Medication(
                profile_id=profile_id,
                name="Metformin Hydrochloride",
                dosage="500 mg",
                frequency="TWICE_DAILY",
                schedule_times=json.dumps(["08:30", "20:30"]),
                food_timing="AFTER_FOOD",
                start_date=today - timedelta(days=60),
                stock_count=28,
                low_stock_threshold=5,
                instructions="Take immediately after morning and evening meals.",
                is_active=True,
                created_by_name="Broly",
                created_by_role="ELDER"
            ),
            Medication(
                profile_id=profile_id,
                name="Telmisartan",
                dosage="40 mg",
                frequency="DAILY",
                schedule_times=json.dumps(["09:00"]),
                food_timing="BEFORE_FOOD",
                start_date=today - timedelta(days=90),
                stock_count=18,
                low_stock_threshold=5,
                instructions="Take once in the morning before breakfast.",
                is_active=True,
                created_by_name="Dr. Ramanathan",
                created_by_role="ELDER"
            ),
            Medication(
                profile_id=profile_id,
                name="Atorvastatin",
                dosage="10 mg",
                frequency="DAILY",
                schedule_times=json.dumps(["21:00"]),
                food_timing="AFTER_FOOD",
                start_date=today - timedelta(days=45),
                stock_count=22,
                low_stock_threshold=5,
                instructions="Take at night after dinner. Avoid grapefruit.",
                is_active=True,
                created_by_name="Broly",
                created_by_role="ELDER"
            ),
            Medication(
                profile_id=profile_id,
                name="Eco-Aspirin",
                dosage="75 mg",
                frequency="DAILY",
                schedule_times=json.dumps(["13:30"]),
                food_timing="AFTER_FOOD",
                start_date=today - timedelta(days=30),
                stock_count=3,  # Demonstrates low stock alert!
                low_stock_threshold=5,
                instructions="Take with water after lunch.",
                is_active=True,
                created_by_name="Priya (Care Nurse)",
                created_by_role="CARETAKER"
            )
        ]
        db.add_all(medications)
        db.commit()

        # 4. Generate Past 14 Days & Today's Dose Logs
        # Demonstrates 14-day patterns: high adherence week 1, and missed evening doses in week 2 (repeated misses pattern)
        for d_offset in range(13, 0, -1):
            past_date = today - timedelta(days=d_offset)
            for med in medications:
                times = med.get_times()
                for t_str in times:
                    h, m = map(int, t_str.split(":"))
                    sched_dt = datetime.combine(past_date, time(h, m))
                    
                    # Scenario: Missed evening doses for 4 consecutive days (d_offset in [1, 2, 3, 4] and evening dose >= 20:00)
                    is_evening_miss = (d_offset in [1, 2, 3, 4] and h >= 20)
                    is_missed = is_evening_miss or (d_offset == 8 and med.name == "Eco-Aspirin")
                    st = "MISSED" if is_missed else "TAKEN"

                    log = DoseLog(
                        profile_id=profile_id,
                        medication_id=med.id,
                        scheduled_time=sched_dt,
                        status=st,
                        taken_at=sched_dt + timedelta(minutes=5) if not is_missed else None,
                        taken_by_name="Broly" if not is_missed else None,
                        escalation_level=1 if is_missed else 0
                    )
                    db.add(log)

        # Today's doses
        # 08:30 Metformin -> TAKEN
        db.add(DoseLog(
            profile_id=profile_id,
            medication_id=medications[0].id,
            scheduled_time=datetime.combine(today, time(8, 30)),
            status="TAKEN",
            taken_at=datetime.combine(today, time(8, 35)),
            taken_by_name="Broly",
            escalation_level=0
        ))
        # 09:00 Telmisartan -> TAKEN
        db.add(DoseLog(
            profile_id=profile_id,
            medication_id=medications[1].id,
            scheduled_time=datetime.combine(today, time(9, 0)),
            status="TAKEN",
            taken_at=datetime.combine(today, time(9, 5)),
            taken_by_name="Broly",
            escalation_level=0
        ))
        # 13:30 Eco-Aspirin -> MISSED (escalation level 1 active)
        db.add(DoseLog(
            profile_id=profile_id,
            medication_id=medications[3].id,
            scheduled_time=datetime.combine(today, time(13, 30)),
            status="MISSED",
            escalation_level=1,
            notes="Elder was resting; reminder email sent"
        ))
        # 20:30 Metformin -> PENDING (Next Dose for Elder!)
        db.add(DoseLog(
            profile_id=profile_id,
            medication_id=medications[0].id,
            scheduled_time=datetime.combine(today, time(20, 30)),
            status="PENDING",
            escalation_level=0
        ))
        # 21:00 Atorvastatin -> PENDING
        db.add(DoseLog(
            profile_id=profile_id,
            medication_id=medications[2].id,
            scheduled_time=datetime.combine(today, time(21, 0)),
            status="PENDING",
            escalation_level=0
        ))
        db.commit()

        # 5. Appointments
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        appts = [
            Appointment(
                profile_id=profile_id,
                doctor_name="K. Ramanathan",
                specialty="Cardiologist",
                appointment_time=datetime.combine(tomorrow, time(10, 30)),
                location="Apollo Heart Centre, Room 204",
                notes="Quarterly blood pressure check and ECG review.",
                is_completed=False,
                created_by_name="Karthik (Son)"
            ),
            Appointment(
                profile_id=profile_id,
                doctor_name="Meenakshi Broly",
                specialty="Diabetologist & Endocrinologist",
                appointment_time=datetime.combine(next_week, time(16, 0)),
                location="Diabetes & Thyroid Clinic, 2nd Cross",
                notes="Review fasting blood glucose and HbA1c test reports.",
                is_completed=False,
                created_by_name="Priya (Care Nurse)"
            )
        ]
        db.add_all(appts)
        db.commit()

        # 6. Pending Change for Elder Review (Center of Healthcare Decisions!)
        pending_item = PendingChange(
            profile_id=profile_id,
            entity_type="MEDICATION",
            action_type="CREATE",
            target_id=None,
            payload=json.dumps({
                "name": "Gabapentin",
                "dosage": "100 mg",
                "frequency": "DAILY",
                "schedule_times": ["21:30"],
                "food_timing": "AFTER_FOOD",
                "start_date": today.isoformat(),
                "stock_count": 30,
                "low_stock_threshold": 5,
                "instructions": "Recommended by neurologist for bedtime leg nerve tingling."
            }),
            status="PENDING",
            proposed_by_name="Priya (Care Nurse)",
            proposed_by_role="CARETAKER"
        )
        db.add(pending_item)
        db.commit()

        # 7. Activity Logs
        activities = [
            ActivityLog(
                profile_id=profile_id,
                action="PROFILE_SETUP",
                details="Elder profile initialized for Broly with passcode protection.",
                performed_by_name="Broly",
                performed_by_role="ELDER"
            ),
            ActivityLog(
                profile_id=profile_id,
                action="MEMBER_JOINED",
                details="Priya (Care Nurse) joined as CARETAKER using designated passcode.",
                performed_by_name="Priya (Care Nurse)",
                performed_by_role="CARETAKER"
            ),
            ActivityLog(
                profile_id=profile_id,
                action="MEMBER_JOINED",
                details="Karthik (Son) joined as FAMILY.",
                performed_by_name="Karthik",
                performed_by_role="FAMILY"
            ),
            ActivityLog(
                profile_id=profile_id,
                action="DOSE_TAKEN",
                details="Broly marked Metformin 500mg as TAKEN.",
                performed_by_name="Broly",
                performed_by_role="ELDER"
            ),
            ActivityLog(
                profile_id=profile_id,
                action="LOW_STOCK_WARNING",
                details="Eco-Aspirin 75mg reached low stock threshold (3 pills remaining).",
                performed_by_name="System",
                performed_by_role="SYSTEM"
            ),
            ActivityLog(
                profile_id=profile_id,
                action="CHANGE_PROPOSED",
                details="Priya (Care Nurse) proposed adding Gabapentin 100mg. Awaiting Elder Broly's approval.",
                performed_by_name="Priya (Care Nurse)",
                performed_by_role="CARETAKER"
            )
        ]
        db.add_all(activities)
        db.commit()

        # 8. Generate Initial AI Care Insights based on the 14-day history
        insights = analyze_profile_insights(db, profile_id, trigger_notifications=True)

        print(" Demo data seeded successfully!")
        print(f"Profile ID:        {profile_id}")
        print("Role Passcodes:")
        print("  👴 Elder:       1111 (Language: Tamil 'ta')")
        print("  🩺 Caretaker:   2222 (Language: English 'en')")
        print("  👨‍👩‍👧 Family:      3333 (Language: Hindi 'hi')")
        print(f"💡 AI Care Insights Generated: {len(insights)} alert(s) dispatched to caretaker & family in their languages.")
        for ins in insights:
            print(f"   [{ins.severity.upper()}] {ins.title_en} - {ins.suggested_action}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
