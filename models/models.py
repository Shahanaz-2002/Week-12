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

class SimilarCase(BaseModel):

    case_id: str = "Unknown"

    diagnosis: str = ""

    symptoms: str = ""

    assessment_notes: str = ""

    doctor_notes: str = ""

    similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    confidence_level: str = "Moderate"

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "diagnosis",
        "symptoms",
        "assessment_notes",
        "doctor_notes",
        mode="before"
    )
    @classmethod
    def clean_text_fields(cls, value):

        return clean_text(value)

    @field_validator("similarity_score")
    @classmethod
    def validate_similarity_score(cls, value):

        return safe_float(value)

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence(cls, value):

        allowed = [
            "Very High",
            "High",
            "Moderate",
            "Low"
        ]

        if value not in allowed:
            return "Moderate"

        return value


# =========================================================
# SIMILAR CASES REQUEST
# =========================================================

class SimilarCasesRequest(BaseModel):

    symptoms: List[str] = Field(
        default_factory=list,
        description="Patient symptoms"
    )

    assessment_notes: str = Field(
        default="",
        description="Clinical assessment notes"
    )

    diagnosis: str = Field(
        default="",
        description="Diagnosis information"
    )

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True
    )

    @field_validator("symptoms", mode="before")
    @classmethod
    def clean_symptoms(cls, value):

        if value is None:
            return []

        if not isinstance(value, list):
            raise ValueError(
                "symptoms must be a list"
            )

        cleaned = []

        for symptom in value:

            symptom = clean_text(symptom)

            if symptom:
                cleaned.append(symptom)

        return cleaned

    @field_validator(
        "assessment_notes",
        "diagnosis",
        mode="before"
    )
    @classmethod
    def clean_string_fields(cls, value):

        return clean_text(value)

    @model_validator(mode="after")
    def validate_request(self):

        if (
            len(self.symptoms) == 0
            and not self.assessment_notes
            and not self.diagnosis
        ):

            raise ValueError(
                "At least one symptom, assessment_notes, or diagnosis is required"
            )

        return self

    def build_search_query(self):

        query_parts = []

        query_parts.extend(self.symptoms)

        if self.assessment_notes:
            query_parts.append(
                self.assessment_notes
            )

        if self.diagnosis:
            query_parts.append(
                self.diagnosis
            )

        return " | ".join(query_parts).strip()


# =========================================================
# SIMILAR CASES RESPONSE
# =========================================================

class SimilarCasesResponse(BaseModel):

    similar_cases: List[SimilarCase] = Field(
        default_factory=list
    )

    similarity_score: List[float] = Field(
        default_factory=list
    )

    total_matches_found: int = 0

    average_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    success: bool = True

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "similarity_score",
        mode="before"
    )
    @classmethod
    def validate_scores(cls, values):

        if not values:
            return []

        return [
            safe_float(v)
            for v in values
        ]

    @field_validator(
        "average_similarity"
    )
    @classmethod
    def validate_average_similarity(
        cls,
        value
    ):

        return safe_float(value)

    @field_validator(
        "total_matches_found"
    )
    @classmethod
    def validate_total_matches(
        cls,
        value
    ):

        try:
            value = int(value)

            if value < 0:
                return 0

            if value > MAX_MATCH_RESULTS:
                return MAX_MATCH_RESULTS

            return value

        except Exception:
            return 0


# =========================================================
# NEW: PHASE 3 - DIAGNOSIS SUGGESTIONS MODEL
# =========================================================

class DiagnosisRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    assessment_notes: Optional[str] = ""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("symptoms", mode="before")
    @classmethod
    def clean_symptoms(cls, value):
        if not isinstance(value, list):
            return []
        return [clean_text(v) for v in value if clean_text(v)]

    @field_validator("assessment_notes", mode="before")
    @classmethod
    def clean_notes(cls, value):
        return clean_text(value)


# =========================================================
# NEW: PHASE 4 - RECOMMENDED TESTS MODEL
# =========================================================

class TestRequest(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    possible_diagnosis: str = ""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("symptoms", mode="before")
    @classmethod
    def clean_symptoms(cls, value):
        if not isinstance(value, list):
            return []
        return [clean_text(v) for v in value if clean_text(v)]

    @field_validator("possible_diagnosis", mode="before")
    @classmethod
    def clean_diagnosis(cls, value):
        return clean_text(value)


# =========================================================
# NEW: PHASE 5 - CARE RECOMMENDATIONS RESPONSE MODEL
# =========================================================

class CareRecommendationResponse(BaseModel):

    home_plan: List[str] = Field(
        default_factory=list,
        description="Home care plan suggestions"
    )

    care_recommendations: List[str] = Field(
        default_factory=list,
        description="Clinical self-care recommendations"
    )

    follow_up_recommendations: List[str] = Field(
        default_factory=list,
        description="Follow-up and referral recommendations"
    )

    success: bool = True

    model_config = ConfigDict(
        extra="ignore"
    )
# =========================================================
# NEW: PHASE 6 - UNIFIED OUTPUT FRAMEWORK MODEL
# =========================================================


class DiagnosisSuggestion(BaseModel):

    diagnosis: str

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    rationale: str = ""

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "diagnosis",
        "rationale",
        mode="before"
    )
    @classmethod
    def clean_text_fields(cls, value):

        return clean_text(value)

    @field_validator("confidence_score")
    @classmethod
    def validate_score(cls, value):

        return safe_float(value)

class HomePlanItem(BaseModel):

    recommendation: str

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "recommendation",
        mode="before"
    )
    @classmethod
    def clean_recommendation(cls, value):

        return clean_text(value)
    
class CareRecommendationItem(BaseModel):

    recommendation: str

    category: str = ""

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "recommendation",
        "category",
        mode="before"
    )
    @classmethod
    def clean_fields(cls, value):

        return clean_text(value)
    
class CareRecommendationRequest(BaseModel):

    symptoms: List[str] = Field(default_factory=list)

    possible_diagnosis: str = ""

    model_config = ConfigDict(
        extra="ignore"
    )
    
class RecommendedTest(BaseModel):

    test_name: str

    rationale: str = ""

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "test_name",
        "rationale",
        mode="before"
    )
    @classmethod
    def clean_fields(cls, value):

        return clean_text(value)

    @field_validator("confidence_score")
    @classmethod
    def validate_score(cls, value):

        return safe_float(value)
class ClinicalIntelligenceResponse(BaseModel):

    similar_cases: List[SimilarCase] = Field(
        default_factory=list
    )

    possible_diagnoses: List[
        DiagnosisSuggestion
    ] = Field(
        default_factory=list
    )

    recommended_tests: List[
        RecommendedTest
    ] = Field(
        default_factory=list
    )

    home_plan: List[
        HomePlanItem
    ] = Field(
        default_factory=list
    )

    care_recommendations: List[
        CareRecommendationItem
    ] = Field(
        default_factory=list
    )

    follow_up_recommendations: List[str] = Field(
        default_factory=list
    )

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    processing_time_ms: float = 0.0

    success: bool = True

    model_config = ConfigDict(
        extra="ignore"
    )

    @field_validator(
        "confidence_score"
    )
    @classmethod
    def validate_confidence(
        cls,
        value
    ):

        return safe_float(value)

    @field_validator(
        "processing_time_ms"
    )
    @classmethod
    def validate_processing_time(
        cls,
        value
    ):

        try:
            value = float(value)

            if value < 0:
                return 0.0

            return round(value, 2)

        except Exception:
            return 0.0