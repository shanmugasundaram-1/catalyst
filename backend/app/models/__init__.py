import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(64), primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False, default=70)
    blood_group = Column(String(16), default="O+")
    emergency_phone = Column(String(32), default="")
    emergency_notes = Column(Text, default="")
    
    # Passcodes for the 3 roles
    elder_passcode_hash = Column(String(255), nullable=False)
    caretaker_passcode_hash = Column(String(255), nullable=False)
    family_passcode_hash = Column(String(255), nullable=False)

    auto_approve_caretaker = Column(Boolean, default=False)
    language = Column(String(8), default="en")  # 'en' or 'ta'
    created_at = Column(DateTime, default=utc_now)

    members = relationship("ProfileMember", back_populates="profile", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="profile", cascade="all, delete-orphan")
    dose_logs = relationship("DoseLog", back_populates="profile", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="profile", cascade="all, delete-orphan")
    pending_changes = relationship("PendingChange", back_populates="profile", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="profile", cascade="all, delete-orphan")
    insights = relationship("CareInsight", back_populates="profile", cascade="all, delete-orphan")


class ProfileMember(Base):
    __tablename__ = "profile_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # ELDER, CARETAKER, FAMILY
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), default="")
    language = Column(String(8), default="en")  # 'en', 'ta', 'hi'
    last_active = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="members")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    dosage = Column(String(64), nullable=False)  # e.g., "500mg"
    frequency = Column(String(32), default="DAILY")  # DAILY, TWICE_DAILY, THRICE_DAILY, WEEKLY, CUSTOM
    schedule_times = Column(Text, default="[\"09:00\"]")  # JSON encoded list of "HH:MM"
    food_timing = Column(String(32), default="AFTER_FOOD")  # BEFORE_FOOD, AFTER_FOOD, WITH_FOOD, ANYTIME
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    stock_count = Column(Integer, default=30)
    low_stock_threshold = Column(Integer, default=5)
    instructions = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_by_name = Column(String(128), default="Elder")
    created_by_role = Column(String(32), default="ELDER")
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="medications")
    dose_logs = relationship("DoseLog", back_populates="medication", cascade="all, delete-orphan")

    def get_times(self):
        try:
            return json.loads(self.schedule_times or "[]")
        except Exception:
            return ["09:00"]


class DoseLog(Base):
    __tablename__ = "dose_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(32), default="PENDING")  # PENDING, TAKEN, MISSED, SKIPPED
    taken_at = Column(DateTime, nullable=True)
    taken_by_name = Column(String(128), nullable=True)
    notes = Column(Text, default="")
    escalation_level = Column(Integer, default=0)  # 0: None, 1: Elder alerted, 2: Caretaker alerted, 3: Family alerted
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="dose_logs")
    medication = relationship("Medication", back_populates="dose_logs")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(128), nullable=False)
    specialty = Column(String(128), default="General Physician")
    appointment_time = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), default="Clinic")
    notes = Column(Text, default="")
    is_completed = Column(Boolean, default=False)
    reminder_sent_24h = Column(Boolean, default=False)
    reminder_sent_2h = Column(Boolean, default=False)
    created_by_name = Column(String(128), default="")
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="appointments")


class PendingChange(Base):
    __tablename__ = "pending_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(32), nullable=False)  # MEDICATION, APPOINTMENT
    action_type = Column(String(32), nullable=False)  # CREATE, UPDATE, DELETE
    target_id = Column(Integer, nullable=True)  # ID of existing medication or appointment if UPDATE/DELETE
    payload = Column(Text, nullable=False)  # JSON payload of the requested change
    status = Column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED
    proposed_by_name = Column(String(128), nullable=False)
    proposed_by_role = Column(String(32), nullable=False)
    proposed_at = Column(DateTime, default=utc_now)
    reviewed_by = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    profile = relationship("Profile", back_populates="pending_changes")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # e.g., DOSE_TAKEN, MED_ADDED, CHANGE_APPROVED, SOS
    details = Column(Text, nullable=False)
    performed_by_name = Column(String(128), nullable=False)
    performed_by_role = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="activity_logs")


class CareInsight(Base):
    __tablename__ = "care_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(64), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_type = Column(String(64), nullable=False)  # REPEATED_MISSES, ADHERENCE_DROP, LOW_STOCK, APPOINTMENT_UNCONFIRMED
    severity = Column(String(16), nullable=False, default="info")  # info, warning, urgent
    title_en = Column(String(255), default="")
    title_ta = Column(String(255), default="")
    title_hi = Column(String(255), default="")
    text_en = Column(Text, nullable=False)
    text_ta = Column(Text, nullable=False)
    text_hi = Column(Text, nullable=False)
    suggested_action = Column(String(255), default="")
    suggested_action_ta = Column(String(255), default="")
    suggested_action_hi = Column(String(255), default="")
    status = Column(String(32), default="ACTIVE")  # ACTIVE, SEEN
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("Profile", back_populates="insights")
