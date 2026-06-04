from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict
)

from typing import (
    Optional,
    Dict,
    Any,
    List
)

import re


# =========================================================
# SAFE TEXT CLEANER
# =========================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = value.strip()

    value = re.sub(r"\s+", " ", value)

    value = re.sub(
        r"[^\w\s,.\-:/()]",
        "",
        value
    )

    return value.strip()


# =========================================================
# REQUEST MODEL
# =========================================================

class ClinicalMatchRequest(BaseModel):

    # =====================================================
    # BASIC PATIENT DETAILS
    # =====================================================

    chief_complaint: Optional[str] = Field(
        default="",
        max_length=500,
        description="Primary complaint reported by the patient"
    )

    affected_body_part: Optional[str] = Field(
        default="",
        max_length=200,
        description="Affected body part or region"
    )

    symptoms_duration: Optional[str] = Field(
        default="",
        max_length=100,
        description="Duration of symptoms"
    )

    previous_injuries: Optional[str] = Field(
        default="",
        max_length=500,
        description="History of previous injuries"
    )

    current_medications: Optional[str] = Field(
        default="",
        max_length=500,
        description="Current medications used by patient"
    )

    allergies: Optional[str] = Field(
        default="",
        max_length=300,
        description="Known allergies"
    )

    occupation: Optional[str] = Field(
        default="",
        max_length=200,
        description="Patient occupation"
    )

    activity_levels: Optional[str] = Field(
        default="",
        max_length=100,
        description="Patient activity levels"
    )

    gender: Optional[str] = Field(
        default="",
        max_length=30,
        description="Patient gender"
    )

    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Patient age"
    )

    doctor_name: Optional[str] = Field(
        default="",
        max_length=100,
        description="Doctor or clinician name"
    )

    # =====================================================
    # CLINICAL DETAILS
    # =====================================================

    subjective_assessment: Optional[str] = Field(
        default="",
        max_length=1500,
        description="Subjective clinical assessment"
    )

    functional_assessment: Optional[str] = Field(
        default="",
        max_length=1500,
        description="Functional limitations or assessment"
    )

    physical_examination: Optional[str] = Field(
        default="",
        max_length=1500,
        description="Physical examination findings"
    )

    objective_findings: Optional[str] = Field(
        default="",
        max_length=1500,
        description="Objective clinical findings"
    )

    patient_pain_classification: Optional[str] = Field(
        default="",
        max_length=100,
        description="Pain severity classification"
    )

    symptoms: Optional[str] = Field(
        default="",
        max_length=2000,
        description="Combined symptom description"
    )

    doctor_notes: Optional[str] = Field(
        default="",
        max_length=3000,
        description="Doctor notes"
    )

    clinical_history: Optional[str] = Field(
        default="",
        max_length=3000,
        description="Complete clinical history"
    )

    additional_findings: Optional[str] = Field(
        default="",
        max_length=2000,
        description="Additional findings"
    )

    medications_history: Optional[str] = Field(
        default="",
        max_length=2000,
        description="Medication history"
    )

    # =====================================================
    # SYSTEM GENERATED FIELDS
    # =====================================================

    search_query: Optional[str] = Field(
        default="",
        description="Generated semantic search query"
    )

    generated_context: Optional[str] = Field(
        default="",
        description="Generated clinical context"
    )

    # =====================================================
    # MODEL CONFIG
    # =====================================================

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True
    )

    # =====================================================
    # FIELD CLEANING
    # =====================================================

    @field_validator(
        "*",
        mode="before"
    )
    @classmethod
    def clean_string_fields(
        cls,
        value
    ):

        if isinstance(value, str):

            value = clean_text(value)

        return value

    # =====================================================
    # GENDER VALIDATION
    # =====================================================

    @field_validator("gender")
    @classmethod
    def validate_gender(
        cls,
        value
    ):

        if value in [None, ""]:

            return ""

        allowed = [

            "male",
            "female",
            "other",
            "prefer not to say"
        ]

        if value.lower() not in allowed:

            raise ValueError(
                "Gender must be Male, Female, Other, or Prefer not to say"
            )

        return value.title()

    # =====================================================
    # AGE VALIDATION
    # =====================================================

    @field_validator("age")
    @classmethod
    def validate_age(
        cls,
        value
    ):

        if value is None:

            return value

        if value < 0 or value > 120:

            raise ValueError(
                "Age must be between 0 and 120"
            )

        return value

    # =====================================================
    # AT LEAST ONE INPUT VALIDATION
    # =====================================================

    @model_validator(mode="after")
    def validate_at_least_one_field(
        self
    ):

        values = self.model_dump()

        non_empty_fields = [

            value

            for value in values.values()

            if value not in [None, "", [], {}]
        ]

        if len(non_empty_fields) == 0:

            raise ValueError(
                "At least one clinical input field is required"
            )

        return self

    # =====================================================
    # AVAILABLE INPUT FIELDS
    # =====================================================

    def get_available_fields(
        self
    ) -> List[str]:

        return [

            field_name

            for field_name, value
            in self.model_dump().items()

            if value not in [None, "", [], {}]
        ]

    # =====================================================
    # SEARCH QUERY GENERATION
    # =====================================================

    def build_search_query(
        self
    ) -> str:

        weighted_fields = [

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
            self.doctor_notes
        ]

        query_parts = []

        for item in weighted_fields:

            cleaned = clean_text(item)

            if cleaned:

                query_parts.append(cleaned)

        search_query = " | ".join(query_parts)

        return search_query.strip()

    # =====================================================
    # CONTEXT GENERATION
    # =====================================================

    def build_context(
        self
    ) -> str:

        context_parts = []

        field_map = {

            "Age": self.age,
            "Gender": self.gender,
            "Occupation": self.occupation,
            "Activity Levels": self.activity_levels,
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
            "Doctor Notes": self.doctor_notes,
            "Clinical History": self.clinical_history,
            "Additional Findings": self.additional_findings,
            "Doctor Name": self.doctor_name
        }

        for key, value in field_map.items():

            if value not in [None, "", [], {}]:

                context_parts.append(
                    f"{key}: {value}"
                )

        return "\n".join(context_parts)

    # =====================================================
    # COMBINED SYMPTOMS
    # =====================================================

    def build_combined_symptoms(
        self
    ) -> str:

        symptom_fields = [

            self.chief_complaint,
            self.subjective_assessment,
            self.objective_findings,
            self.physical_examination,
            self.symptoms,
            self.patient_pain_classification
        ]

        combined = " | ".join([

            clean_text(item)

            for item in symptom_fields

            if item not in [None, ""]
        ])

        return combined.strip()

    # =====================================================
    # PATIENT METADATA
    # =====================================================

    def build_patient_metadata(
        self
    ) -> Dict[str, Any]:

        return {

            "age": self.age,

            "gender": self.gender,

            "occupation": self.occupation,

            "activity_levels": self.activity_levels,

            "doctor_name": self.doctor_name
        }

    # =====================================================
    # DYNAMIC INPUT GENERATION
    # =====================================================

    def generate_dynamic_inputs(
        self
    ) -> Dict[str, Any]:

        search_query = (
            self.build_search_query()
        )

        generated_context = (
            self.build_context()
        )

        combined_symptoms = (
            self.build_combined_symptoms()
        )

        patient_metadata = (
            self.build_patient_metadata()
        )

        available_fields = (
            self.get_available_fields()
        )

        return {

            "search_query":
                search_query,

            "generated_context":
                generated_context,

            "combined_symptoms":
                combined_symptoms,

            "patient_metadata":
                patient_metadata,

            "available_fields":
                available_fields
        }