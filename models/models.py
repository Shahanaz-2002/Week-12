# =========================================================
# models/models.py
# =========================================================

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict
)

from typing import (
    List,
    Optional,
    Dict,
    Any
)

import re
import logging

from datetime import datetime, timezone

from config import (
    MAX_MATCH_RESULTS,
    ALLOWED_GENDERS
)

# =========================================================
# SAFE TEXT CLEANER
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    # improved regex (keeps medical-relevant symbols)
    value = re.sub(
        r"[^\w\s.,\-:/()%+×°]",
        "",
        value
    )

    return value.strip()


# =========================================================
# SAFE LIST
# =========================================================

def safe_list(value):
    if isinstance(value, list):
        return value
    return []


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value):
    try:
        value = float(value)
        value = max(0.0, min(value, 1.0))
        return round(value, 4)

    except Exception:
        logging.warning(f"Invalid float value received: {value}")
        return 0.0


# =========================================================
# HELPER
# =========================================================

def is_empty(v):
    return v is None or v == "" or v == [] or v == {}


# =========================================================
# PATIENT METADATA MODEL
# =========================================================

class PatientMetadata(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=120)
    gender: Optional[str] = ""
    occupation: Optional[str] = ""
    activity_levels: Optional[str] = ""
    doctor_name: Optional[str] = ""

    model_config = ConfigDict(extra="ignore")


# =========================================================
# REQUEST MODEL
# =========================================================

class ClinicalMatchRequest(BaseModel):

    # BASIC DETAILS
    chief_complaint: Optional[str] = ""
    affected_body_part: Optional[str] = ""
    symptoms_duration: Optional[str] = ""
    previous_injuries: Optional[str] = ""
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""
    occupation: Optional[str] = ""
    activity_levels: Optional[str] = ""
    gender: Optional[str] = ""
    age: Optional[int] = Field(default=None, ge=0, le=120)
    doctor_name: Optional[str] = ""

    # CLINICAL DETAILS
    subjective_assessment: Optional[str] = ""
    functional_assessment: Optional[str] = ""
    physical_examination: Optional[str] = ""
    objective_findings: Optional[str] = ""
    patient_pain_classification: Optional[str] = ""
    symptoms: Optional[str] = ""
    doctor_notes: Optional[str] = ""
    clinical_history: Optional[str] = ""
    additional_findings: Optional[str] = ""
    medications_history: Optional[str] = ""

    # DERMATOLOGY SUPPORT
    skin_condition: Optional[str] = ""
    affected_skin_area: Optional[str] = ""
    skin_type: Optional[str] = ""
    previous_skin_conditions: Optional[str] = ""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True
    )

    # =====================================================
    # FIELD CLEANING
    # =====================================================

    @field_validator("*", mode="before")
    @classmethod
    def clean_fields(cls, value):
        if isinstance(value, str):
            value = clean_text(value)
            if len(value) > 2000:
                value = value[:2000]
        return value

    # =====================================================
    # GENDER VALIDATION
    # =====================================================

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value):

        if not value:
            return ""

        allowed = {g.lower() for g in ALLOWED_GENDERS}

        if value.lower() not in allowed:
            raise ValueError(
                f"Invalid gender value. Allowed: {ALLOWED_GENDERS}"
            )

        return value.capitalize()

    # =====================================================
    # MINIMUM INPUT VALIDATION
    # =====================================================

    @model_validator(mode="after")
    def validate_input(self):

        values = self.model_dump()

        non_empty = [
            v for v in values.values()
            if not is_empty(v)
        ]

        if len(non_empty) == 0:
            raise ValueError("At least one clinical field is required")

        return self

    # =====================================================
    # SEARCH QUERY GENERATION
    # =====================================================

    def build_search_query(self):

        fields = [
            self.chief_complaint,
            self.affected_body_part,
            self.symptoms,
            self.subjective_assessment,
            self.functional_assessment,
            self.physical_examination,
            self.objective_findings,
            self.patient_pain_classification,
            self.previous_injuries,
            self.clinical_history,
            self.additional_findings,
            self.skin_condition,
            self.affected_skin_area,
            self.skin_type,
            self.previous_skin_conditions
        ]

        cleaned_fields = [
            clean_text(x)
            for x in fields
            if x and str(x).strip()
        ]

        return " | ".join(cleaned_fields).strip()

    # =====================================================
    # CONTEXT GENERATION
    # =====================================================

    def build_context(self):

        field_map = {
            "Age": self.age,
            "Gender": self.gender,
            "Occupation": self.occupation,
            "Activity Levels": self.activity_levels,
            "Doctor Name": self.doctor_name,
            "Chief Complaint": self.chief_complaint,
            "Affected Body Part": self.affected_body_part,
            "Symptoms Duration": self.symptoms_duration,
            "Symptoms": self.symptoms,
            "Subjective Assessment": self.subjective_assessment,
            "Functional Assessment": self.functional_assessment,
            "Physical Examination": self.physical_examination,
            "Objective Findings": self.objective_findings,
            "Pain Classification": self.patient_pain_classification,
            "Previous Injuries": self.previous_injuries,
            "Current Medications": self.current_medications,
            "Allergies": self.allergies,
            "Clinical History": self.clinical_history,
            "Doctor Notes": self.doctor_notes,
            "Additional Findings": self.additional_findings,
            "Skin Condition": self.skin_condition,
            "Affected Skin Area": self.affected_skin_area,
            "Skin Type": self.skin_type,
            "Previous Skin Conditions": self.previous_skin_conditions
        }

        context = []

        for key, value in field_map.items():
            if not is_empty(value):
                context.append(f"{key}: {value}")

        return "\n".join(context)

    # =====================================================
    # AVAILABLE FIELDS
    # =====================================================

    def get_available_fields(self):

        return [
            k for k, v in self.model_dump().items()
            if not is_empty(v)
        ]

    # =====================================================
    # PATIENT METADATA
    # =====================================================

    def get_patient_metadata(self):

        return {
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "activity_levels": self.activity_levels,
            "doctor_name": self.doctor_name
        }

    # =====================================================
    # DYNAMIC INPUT PROCESSOR
    # =====================================================

    def generate_dynamic_inputs(self):

        search_query = self.build_search_query()
        generated_context = self.build_context()

        combined_symptoms = " | ".join([
            x for x in [
                self.symptoms,
                self.chief_complaint,
                self.patient_pain_classification,
                self.subjective_assessment,
                self.objective_findings,
                self.skin_condition
            ]
            if x and str(x).strip()
        ])

        return {
            "search_query": search_query,
            "generated_context": generated_context,
            "combined_symptoms": combined_symptoms,
            "patient_metadata": self.get_patient_metadata(),
            "available_fields": self.get_available_fields()
        }


# =========================================================
# RECOMMENDATION MODEL
# =========================================================

class RecommendationModel(BaseModel):

    recommended_tests: List[str] = Field(default_factory=list)
    recommended_medicines: List[str] = Field(default_factory=list)
    recommendation_notes: str = ""
    physiotherapy_plan: List[str] = Field(default_factory=list)
    precautions: List[str] = Field(default_factory=list)
    skincare_plan: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


# =========================================================
# MATCH RESULT MODEL
# =========================================================

class MatchResult(BaseModel):

    case_id: str

    match_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(default=0.0, ge=0.0, le=1.0)

    confidence_level: str = "Moderate"
    retrieval_source: str = "BioBERT Semantic Search"

    chief_complaint: str = "Unknown"
    affected_body_part: str = "Unknown"
    symptoms_duration: str = "Unknown"
    doctor_notes: str = "No notes available"
    clinical_history: str = ""

    matched_keywords: List[str] = Field(default_factory=list)
    searchable_text: str = ""

    explanation: str = "Match generated using semantic similarity"

    recommendation: RecommendationModel

    case_data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence(cls, value):

        allowed = ["High", "Moderate", "Low"]
        if value not in allowed:
            return "Moderate"
        return value

    @field_validator("match_score", "semantic_score")
    @classmethod
    def validate_scores(cls, value):
        return safe_float(value)


# =========================================================
# FINAL RESPONSE MODEL
# =========================================================

class ClinicalMatchResponse(BaseModel):

    status: str
    message: str
    request_id: str

    api_version: str = "6.0.0"

    request_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    matches: List[MatchResult] = Field(default_factory=list)

    total_matches_found: int = 0

    confidence_score: float = Field(ge=0.0, le=1.0)

    search_query: str = ""
    generated_context: str = ""
    combined_symptoms: str = ""

    input_fields_used: List[str] = Field(default_factory=list)

    processing_time_ms: float = 0.0

    patient_metadata: Dict[str, Any] = Field(default_factory=dict)

    explanation: str = ""

    warnings: List[str] = Field(default_factory=list)

    success: bool = True

    model_config = ConfigDict(extra="ignore")

    @field_validator("total_matches_found")
    @classmethod
    def validate_total_matches(cls, value):
        if value < 0:
            return 0
        if value > MAX_MATCH_RESULTS:
            return MAX_MATCH_RESULTS
        return value

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, value):
        return safe_float(value)

    @field_validator("processing_time_ms")
    @classmethod
    def validate_processing_time(cls, value):
        try:
            value = float(value)
            if value < 0:
                return 0.0
            return round(value, 2)
        except Exception:
            return 0.0


# =========================================================
# SIMILAR CASES MODELS
# =========================================================

class SimilarCasesRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    assessment_notes: str = ""
    diagnosis: str = ""


class SimilarCasesResponse(BaseModel):
    similar_cases: List[Dict[str, Any]] = Field(default_factory=list)
    similarity_score: List[float] = Field(default_factory=list)