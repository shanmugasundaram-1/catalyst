from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, date

# --- Auth Schemas ---
class JoinProfileRequest(BaseModel):
    profile_id: str = Field(..., description="The unique profile ID of the elder (e.g. 'ELDER-DEMO')")
    passcode: str = Field(..., description="The 4 or 6 digit role passcode")
    name: str = Field(..., description="Your display name (e.g. 'Dr. Sarah', 'Grandpa Arun', 'Son Ramesh')")
    email: str = Field(..., description="Your email address to receive alerts and summaries")
    phone: Optional[str] = ""
    language: Optional[str] = None

class CreateProfileRequest(BaseModel):
    full_name: str
    age: int = 72
    blood_group: str = "O+"
    emergency_phone: str = ""
    emergency_notes: str = ""
    elder_passcode: str = "1111"
    caretaker_passcode: str = "2222"
    family_passcode: str = "3333"
    auto_approve_caretaker: bool = False
    language: str = "en"
    creator_name: str = "Self"
    creator_email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str
    profile_id: str
    profile_name: str
    language: str
    auto_approve_caretaker: bool

class CurrentUser(BaseModel):
    profile_id: str
    role: str  # ELDER, CARETAKER, FAMILY
    name: str
    email: str
    language: str = "en"

# --- Profile Schemas ---
class UpdateMemberLanguageRequest(BaseModel):
    language: str = Field(..., description="'en', 'ta', or 'hi'")

class ProfileSettingsUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_notes: Optional[str] = None
    auto_approve_caretaker: Optional[bool] = None
    language: Optional[str] = None
    elder_passcode: Optional[str] = None
    caretaker_passcode: Optional[str] = None
    family_passcode: Optional[str] = None

class ProfileMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    role: str
    language: str = "en"
    last_active: datetime

    model_config = ConfigDict(from_attributes=True)

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    age: int
    blood_group: str
    emergency_phone: str
    emergency_notes: str
    auto_approve_caretaker: bool
    language: str
    created_at: datetime
    members: List[ProfileMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Medication Schemas ---
class MedicationCreate(BaseModel):
    name: str
    dosage: str  # e.g. "500 mg"
    frequency: str = "DAILY"  # DAILY, TWICE_DAILY, THRICE_DAILY, WEEKLY, CUSTOM
    schedule_times: List[str] = ["09:00"]  # ["09:00", "21:00"]
    food_timing: str = "AFTER_FOOD"  # BEFORE_FOOD, AFTER_FOOD, WITH_FOOD, ANYTIME
    start_date: date
    end_date: Optional[date] = None
    stock_count: int = 30
    low_stock_threshold: int = 5
    instructions: Optional[str] = ""

class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    schedule_times: Optional[List[str]] = None
    food_timing: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    stock_count: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None

class MedicationResponse(BaseModel):
    id: int
    profile_id: str
    name: str
    dosage: str
    frequency: str
    schedule_times: List[str]
    food_timing: str
    start_date: date
    end_date: Optional[date]
    stock_count: int
    low_stock_threshold: int
    instructions: str
    is_active: bool
    created_by_name: str
    created_by_role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Dose Log Schemas ---
class DoseActionRequest(BaseModel):
    status: str  # TAKEN, SKIPPED, MISSED
    notes: Optional[str] = ""

class DoseLogResponse(BaseModel):
    id: int
    profile_id: str
    medication_id: int
    medication_name: str
    dosage: str
    food_timing: str
    scheduled_time: datetime
    status: str
    taken_at: Optional[datetime]
    taken_by_name: Optional[str]
    notes: Optional[str]
    escalation_level: int

    model_config = ConfigDict(from_attributes=True)

class TodayOverviewResponse(BaseModel):
    next_dose: Optional[DoseLogResponse] = None
    today_doses: List[DoseLogResponse] = []
    adherence_percentage: float = 100.0
    streak_days: int = 0
    total_scheduled: int = 0
    total_taken: int = 0
    total_missed: int = 0

# --- Appointment Schemas ---
class AppointmentCreate(BaseModel):
    doctor_name: str
    specialty: str = "General Physician"
    appointment_time: datetime
    location: str = "City Clinic"
    notes: Optional[str] = ""

class AppointmentUpdate(BaseModel):
    doctor_name: Optional[str] = None
    specialty: Optional[str] = None
    appointment_time: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_completed: Optional[bool] = None

class AppointmentResponse(BaseModel):
    id: int
    profile_id: str
    doctor_name: str
    specialty: str
    appointment_time: datetime
    location: str
    notes: str
    is_completed: bool
    created_by_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Pending Change Schemas (Elder Approval) ---
class PendingChangeResponse(BaseModel):
    id: int
    profile_id: str
    entity_type: str  # MEDICATION, APPOINTMENT
    action_type: str  # CREATE, UPDATE, DELETE
    target_id: Optional[int]
    payload: dict
    status: str  # PENDING, APPROVED, REJECTED
    proposed_by_name: str
    proposed_by_role: str
    proposed_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class PendingChangeReview(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    rejection_reason: Optional[str] = None

# --- Activity Log Schemas ---
class ActivityLogResponse(BaseModel):
    id: int
    profile_id: str
    action: str
    details: str
    performed_by_name: str
    performed_by_role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- AI Schemas ---
class ExtractedMedication(BaseModel):
    name: str
    dosage: str
    frequency: str = "DAILY"
    schedule_times: List[str] = ["09:00"]
    food_timing: str = "AFTER_FOOD"
    duration_days: Optional[int] = 30
    instructions: str = ""

class PrescriptionScanResponse(BaseModel):
    doctor_name: Optional[str] = "Prescribing Doctor"
    date_prescribed: Optional[str] = None
    diagnosis_or_notes: Optional[str] = ""
    medications: List[ExtractedMedication] = []
    raw_ai_text: Optional[str] = ""

class NaturalLanguageMedRequest(BaseModel):
    text: str = Field(..., description="e.g. 'Metformin 500mg morning and night after food for 30 days'")

class DrugInteractionRequest(BaseModel):
    new_medicine: str
    current_medicines: Optional[List[str]] = None

class InteractionWarning(BaseModel):
    severity: str  # NONE, MILD, MODERATE, SEVERE
    title: str
    description: str
    food_advice: Optional[str] = None

class DrugInteractionResponse(BaseModel):
    has_warning: bool
    overall_status: str  # SAFE, CAUTION, HIGH_RISK
    warnings: List[InteractionWarning] = []
    food_considerations: List[str] = []
    disclaimer: str = "This AI safety check is for guidance only. Always consult your prescribing doctor or certified pharmacist before modifying your medication regimen."

class WeeklySummaryResponse(BaseModel):
    start_date: str
    end_date: str
    elder_name: str
    adherence_percentage: float
    taken_count: int
    missed_count: int
    upcoming_appointments: List[str]
    friendly_summary_en: str
    friendly_summary_ta: str
    friendly_summary_hi: str
    doctor_talking_points: List[str]

# --- Voice Assistant Schemas ---
class VoiceIntentRequest(BaseModel):
    query: str = Field(..., description="Spoken or typed voice query in Hindi, Tamil, or English (including Tanglish/Hinglish)")
    language: Optional[str] = Field("en", description="User's preferred language: 'en', 'ta', or 'hi'")
    confirmed_sos: Optional[bool] = Field(False, description="Whether emergency SOS dispatch was explicitly confirmed by voice or tap")

class VoiceIntentResponse(BaseModel):
    intent: str  # MARK_DOSE_TAKEN, NEXT_DOSE_QUERY, APPOINTMENT_QUERY, SOS, UNKNOWN
    reply_text: str  # Responds in the same language spoken / requested
    spoken_language: str  # 'hi', 'ta', or 'en'
    action_performed: Optional[str] = None
    requires_confirmation: bool = False
    data: Optional[dict] = None

# --- Care Insights Schemas ---
class CareInsightResponse(BaseModel):
    id: int
    profile_id: str
    insight_type: str
    severity: str  # info, warning, urgent
    title_en: str
    title_ta: str
    title_hi: str
    text_en: str
    text_ta: str
    text_hi: str
    suggested_action: str
    suggested_action_ta: str
    suggested_action_hi: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- SOS Schemas ---
class SOSRequest(BaseModel):
    location_note: Optional[str] = "Home"

class SOSResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime
    recipients_notified: List[str]
