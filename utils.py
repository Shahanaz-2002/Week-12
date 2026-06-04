# =========================================================
# utils.py
# =========================================================

import pandas as pd
import logging
import json
import re
import time

from typing import (
    Dict,
    Any,
    List
)

from config import (
    EMBEDDING_VERSION,
    DEFAULT_RECOMMENDED_TESTS,
    DEFAULT_RECOMMENDED_MEDICINES,
    DEFAULT_SKINCARE_PLAN,
    DEFAULT_PRECAUTIONS
)

# =========================================================
# LOGGER CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# =========================================================
# LOGGING HELPER
# =========================================================

def log_event(
    event_type,
    message,
    extra=None
):

    log_data = {

        "event": event_type,

        "message": message,

        "timestamp":
            time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }

    if extra:
        log_data.update(extra)

    logger.info(
        json.dumps(log_data)
    )

# =========================================================
# TEXT CLEANER
# =========================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"[^\w\s,.\-:/()]",
        "",
        text
    )

    return text

# =========================================================
# SAFE INTEGER CONVERSION
# =========================================================

def safe_int(value, default=0):

    try:

        if value in [None, "", "nan"]:
            return default

        return int(float(value))

    except Exception:

        return default

# =========================================================
# SAFE FLOAT CONVERSION
# =========================================================

def safe_float(value, default=0.0):

    try:

        if value in [None, "", "nan"]:
            return default

        return float(value)

    except Exception:

        return default

# =========================================================
# EMPTY VALUE CHECK
# =========================================================

def is_empty(value):

    return value in [
        None,
        "",
        [],
        {},
        "nan",
        "None"
    ]

# =========================================================
# BUILD SEARCH QUERY
# =========================================================

def build_search_query(
    clinical_data: Dict[str, Any]
) -> str:

    query_parts = [

        clean_text(
            clinical_data.get(
                "skin_condition",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "affected_skin_area",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "symptoms",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "skin_type",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "physical_examination",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "objective_findings",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "doctor_notes",
                ""
            )
        ),

        clean_text(
            clinical_data.get(
                "clinical_history",
                ""
            )
        )
    ]

    filtered_parts = [

        part
        for part in query_parts
        if part
    ]

    return " | ".join(
        filtered_parts
    )

# =========================================================
# CONTEXT GENERATION
# =========================================================

def generate_context(
    clinical_data: Dict[str, Any]
) -> str:

    context_parts = []

    field_mapping = {

        "age": "Age",

        "gender": "Gender",

        "occupation": "Occupation",

        "skin_type": "Skin Type",

        "skin_condition":
            "Skin Condition",

        "affected_skin_area":
            "Affected Skin Area",

        "symptoms":
            "Symptoms",

        "symptoms_duration":
            "Symptoms Duration",

        "physical_examination":
            "Physical Examination",

        "objective_findings":
            "Objective Findings",

        "doctor_notes":
            "Doctor Notes",

        "clinical_history":
            "Clinical History",

        "allergies":
            "Allergies",

        "current_medications":
            "Current Medications",

        "doctor_name":
            "Doctor Name"
    }

    for field, label in field_mapping.items():

        value = clean_text(
            clinical_data.get(
                field,
                ""
            )
        )

        if value:

            context_parts.append(
                f"{label}: {value}"
            )

    return "\n".join(
        context_parts
    )

# =========================================================
# DERMATOLOGY KEYWORD EXTRACTION
# =========================================================

def extract_dermatology_keywords(
    text: str
) -> List[str]:

    if not text:
        return []

    text = clean_text(text).lower()

    dermatology_keywords = [

        "acne",
        "eczema",
        "psoriasis",
        "fungal infection",
        "rosacea",
        "dermatitis",
        "urticaria",
        "melasma",
        "vitiligo",
        "rash",
        "itching",
        "redness",
        "dry skin",
        "oily skin",
        "hyperpigmentation",
        "papules",
        "pustules",
        "comedones",
        "scaling",
        "skin irritation",
        "allergic reaction",
        "skin peeling",
        "blisters",
        "lesions",
        "tinea",
        "scabies"
    ]

    found_keywords = []

    for keyword in dermatology_keywords:

        if keyword in text:

            found_keywords.append(
                keyword
            )

    return list(
        set(found_keywords)
    )

# =========================================================
# BUILD SEARCHABLE TEXT
# =========================================================

def build_searchable_text(
    case_data: Dict[str, Any]
) -> str:

    searchable_fields = [

        "skin_condition",

        "affected_skin_area",

        "symptoms",

        "doctor_notes",

        "physical_examination",

        "objective_findings",

        "clinical_history",

        "skin_type",

        "current_medications",

        "allergies"
    ]

    text_parts = []

    for field in searchable_fields:

        value = clean_text(
            case_data.get(
                field,
                ""
            )
        )

        if value:

            text_parts.append(
                value
            )

    return " | ".join(
        text_parts
    )

# =========================================================
# VALIDATE CASE RECORD
# =========================================================

def validate_case_record(
    case_record: Dict[str, Any]
) -> bool:

    required_fields = [

        "case_id",
        "skin_condition"
    ]

    for field in required_fields:

        value = case_record.get(field)

        if is_empty(value):

            return False

    return True

# =========================================================
# NORMALIZE CASE RECORD
# =========================================================

def normalize_case_record(
    case_record: Dict[str, Any]
) -> Dict[str, Any]:

    normalized_record = {}

    for key, value in case_record.items():

        if isinstance(value, str):

            normalized_record[key] = clean_text(
                value
            )

        else:

            normalized_record[key] = value

    return normalized_record

# =========================================================
# GENERATE DEFAULT RECOMMENDATIONS
# =========================================================

def generate_default_recommendations():

    return {

        "recommended_tests":
            DEFAULT_RECOMMENDED_TESTS,

        "recommended_medicines":
            DEFAULT_RECOMMENDED_MEDICINES,

        "skincare_plan":
            DEFAULT_SKINCARE_PLAN,

        "precautions":
            DEFAULT_PRECAUTIONS
    }

# =========================================================
# CSV LOADER
# =========================================================

def load_cases_from_csv(
    file_path: str
) -> Dict[str, Dict[str, Any]]:

    try:

        df = pd.read_csv(
            file_path
        )

        df = df.fillna("")

        case_database = {}

        skipped_records = 0

        log_event(
            "csv_loading_started",
            "Loading dermatology CSV",
            {
                "file_path": file_path,
                "rows": len(df)
            }
        )

        for _, row in df.iterrows():

            try:

                case_id = clean_text(
                    row.get(
                        "case_id",
                        ""
                    )
                )

                if not case_id:

                    skipped_records += 1
                    continue

                recommendations = (
                    generate_default_recommendations()
                )

                case_record = {

                    "case_id":
                        case_id,

                    "skin_condition":
                        clean_text(
                            row.get(
                                "skin_condition",
                                ""
                            )
                        ),

                    "affected_skin_area":
                        clean_text(
                            row.get(
                                "affected_skin_area",
                                ""
                            )
                        ),

                    "symptoms":
                        clean_text(
                            row.get(
                                "symptoms",
                                ""
                            )
                        ),

                    "skin_type":
                        clean_text(
                            row.get(
                                "skin_type",
                                ""
                            )
                        ),

                    "doctor_notes":
                        clean_text(
                            row.get(
                                "doctor_notes",
                                ""
                            )
                        ),

                    "physical_examination":
                        clean_text(
                            row.get(
                                "physical_examination",
                                ""
                            )
                        ),

                    "objective_findings":
                        clean_text(
                            row.get(
                                "objective_findings",
                                ""
                            )
                        ),

                    "clinical_history":
                        clean_text(
                            row.get(
                                "clinical_history",
                                ""
                            )
                        ),

                    "current_medications":
                        clean_text(
                            row.get(
                                "current_medications",
                                ""
                            )
                        ),

                    "allergies":
                        clean_text(
                            row.get(
                                "allergies",
                                ""
                            )
                        ),

                    "symptoms_duration":
                        clean_text(
                            row.get(
                                "symptoms_duration",
                                ""
                            )
                        ),

                    "gender":
                        clean_text(
                            row.get(
                                "gender",
                                ""
                            )
                        ),

                    "age":
                        safe_int(
                            row.get(
                                "age",
                                0
                            )
                        ),

                    "doctor_name":
                        clean_text(
                            row.get(
                                "doctor_name",
                                ""
                            )
                        ),

                    "occupation":
                        clean_text(
                            row.get(
                                "occupation",
                                ""
                            )
                        ),

                    "recommended_tests":
                        recommendations[
                            "recommended_tests"
                        ],

                    "recommended_medicines":
                        recommendations[
                            "recommended_medicines"
                        ],

                    "skincare_plan":
                        recommendations[
                            "skincare_plan"
                        ],

                    "precautions":
                        recommendations[
                            "precautions"
                        ]
                }

                case_record = normalize_case_record(
                    case_record
                )

                if not validate_case_record(
                    case_record
                ):

                    skipped_records += 1

                    continue

                case_record[
                    "search_query"
                ] = build_search_query(
                    case_record
                )

                case_record[
                    "generated_context"
                ] = generate_context(
                    case_record
                )

                case_record[
                    "searchable_text"
                ] = build_searchable_text(
                    case_record
                )

                case_record[
                    "dermatology_keywords"
                ] = extract_dermatology_keywords(
                    case_record[
                        "searchable_text"
                    ]
                )

                case_record[
                    "embedding"
                ] = []

                case_record[
                    "embedding_version"
                ] = EMBEDDING_VERSION

                case_record[
                    "embedding_model"
                ] = (
                    "BioBERT"
                )

                case_record[
                    "embedding_text"
                ] = case_record[
                    "searchable_text"
                ]

                case_database[
                    case_id
                ] = case_record

            except Exception as row_error:

                skipped_records += 1

                log_event(
                    "row_processing_error",
                    "CSV row processing failed",
                    {
                        "error":
                            str(row_error)
                    }
                )

                continue

        log_event(
            "csv_loading_completed",
            "Dermatology CSV loaded successfully",
            {
                "total_cases":
                    len(case_database),

                "skipped_records":
                    skipped_records
            }
        )

        return case_database

    except FileNotFoundError:

        log_event(
            "csv_file_not_found",
            "CSV file not found",
            {
                "file_path":
                    file_path
            }
        )

        return {}

    except pd.errors.EmptyDataError:

        log_event(
            "csv_empty",
            "CSV file empty",
            {
                "file_path":
                    file_path
            }
        )

        return {}

    except Exception as e:

        log_event(
            "csv_loading_error",
            "Failed to load dermatology CSV",
            {
                "error": str(e),
                "file_path": file_path
            }
        )

        return {}