# =========================================================
# services/analyze_service.py
# FINAL STABLE VERSION
# =========================================================

import time
import traceback
import re
import logging

from typing import Dict, List, Any

from fastapi import HTTPException

from retrieval.retrieval_engine import (
    retrieve_similar_cases
)

from retrieval.database import (
    fetch_case_database
)

from config import (

    TOP_K,

    MAX_MATCH_RESULTS,

    VERY_HIGH_CONFIDENCE,

    HIGH_CONFIDENCE,

    MEDIUM_CONFIDENCE,

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

    format="%(asctime)s - %(levelname)s - %(message)s",

    force=True
)

logger = logging.getLogger(__name__)


# =========================================================
# SAFE TEXT HELPER
# =========================================================

def safe_text(value) -> str:

    if value in [None, "", [], {}]:

        return ""

    return str(value).strip()


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(text: str) -> str:

    text = safe_text(text)

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^\w\s|,./()-]", " ", text)

    return text.strip()


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(values: List[str]) -> List[str]:

    seen = set()

    cleaned = []

    for value in values:

        normalized = normalize_text(
            value
        ).lower()

        if normalized and normalized not in seen:

            seen.add(normalized)

            cleaned.append(value)

    return cleaned


# =========================================================
# SAFE ATTRIBUTE ACCESS
# =========================================================

def safe_attr(obj, field_name):

    try:

        return getattr(obj, field_name, "")

    except Exception:

        return ""


# =========================================================
# BUILD SEARCH QUERY
# =========================================================

def build_search_query(request) -> str:

    query_parts = []

    weighted_fields = [

        # =================================================
        # DERMATOLOGY FIELDS
        # =================================================

        safe_attr(request, "skin_condition"),

        safe_attr(request, "affected_skin_area"),

        safe_attr(request, "skin_type"),

        safe_attr(request, "symptoms"),

        safe_attr(request, "subjective_assessment"),

        safe_attr(request, "physical_examination"),

        safe_attr(request, "objective_findings"),

        safe_attr(request, "previous_skin_conditions"),

        safe_attr(request, "allergies"),

        safe_attr(request, "doctor_notes"),

        safe_attr(request, "clinical_history"),

        # =================================================
        # GENERIC CLINICAL SUPPORT
        # =================================================

        safe_attr(request, "chief_complaint"),

        safe_attr(request, "affected_body_part")
    ]

    for field in weighted_fields:

        cleaned = normalize_text(field)

        if cleaned:

            query_parts.append(cleaned)

    query_parts = remove_duplicates(
        query_parts
    )

    return " | ".join(query_parts).strip()


# =========================================================
# BUILD CONTEXT
# =========================================================

def build_clinical_context(request) -> str:

    context_parts = []

    field_mapping = {

        "Age":
            safe_attr(request, "age"),

        "Gender":
            safe_attr(request, "gender"),

        "Occupation":
            safe_attr(request, "occupation"),

        "Skin Type":
            safe_attr(request, "skin_type"),

        "Skin Condition":
            safe_attr(request, "skin_condition"),

        "Affected Skin Area":
            safe_attr(request, "affected_skin_area"),

        "Symptoms":
            safe_attr(request, "symptoms"),

        "Symptoms Duration":
            safe_attr(request, "symptoms_duration"),

        "Previous Skin Conditions":
            safe_attr(request, "previous_skin_conditions"),

        "Allergies":
            safe_attr(request, "allergies"),

        "Doctor Notes":
            safe_attr(request, "doctor_notes"),

        "Clinical History":
            safe_attr(request, "clinical_history"),

        # =================================================
        # GENERIC CLINICAL FIELDS
        # =================================================

        "Chief Complaint":
            safe_attr(request, "chief_complaint"),

        "Affected Body Part":
            safe_attr(request, "affected_body_part")
    }

    for field_name, value in field_mapping.items():

        cleaned = normalize_text(value)

        if cleaned:

            context_parts.append(
                f"{field_name}: {cleaned}"
            )

    return "\n".join(context_parts)


# =========================================================
# GENERATE RECOMMENDATIONS
# =========================================================

def generate_recommendations(
    case
) -> Dict[str, List[str]]:

    recommendations = {

        "recommended_tests": [],

        "recommended_medicines": [],

        "skincare_plan": [],

        "precautions": []
    }

    combined_text = (

        safe_text(
            case.get("skin_condition")
        )

        + " " +

        safe_text(
            case.get("symptoms")
        )

        + " " +

        safe_text(
            case.get("doctor_notes")
        )

    ).lower()

    # =====================================================
    # ACNE
    # =====================================================

    if "acne" in combined_text:

        recommendations["recommended_tests"] = [

            "Dermatoscopy",

            "Hormonal Evaluation"
        ]

        recommendations["recommended_medicines"] = [

            "Benzoyl Peroxide",

            "Topical Retinoid"
        ]

    # =====================================================
    # ECZEMA
    # =====================================================

    elif "eczema" in combined_text:

        recommendations["recommended_tests"] = [

            "Patch Allergy Test"
        ]

        recommendations["recommended_medicines"] = [

            "Topical Corticosteroid",

            "Moisturizer"
        ]

    # =====================================================
    # PSORIASIS
    # =====================================================

    elif "psoriasis" in combined_text:

        recommendations["recommended_tests"] = [

            "Skin Biopsy"
        ]

        recommendations["recommended_medicines"] = [

            "Topical Steroids"
        ]

    # =====================================================
    # FUNGAL
    # =====================================================

    elif (

        "fungal" in combined_text or
        "tinea" in combined_text

    ):

        recommendations["recommended_tests"] = [

            "KOH Examination"
        ]

        recommendations["recommended_medicines"] = [

            "Clotrimazole",

            "Ketoconazole"
        ]

    # =====================================================
    # DEFAULT
    # =====================================================

    else:

        recommendations["recommended_tests"] = (
            DEFAULT_RECOMMENDED_TESTS
        )

        recommendations["recommended_medicines"] = (
            DEFAULT_RECOMMENDED_MEDICINES
        )

    recommendations["skincare_plan"] = (
        DEFAULT_SKINCARE_PLAN
    )

    recommendations["precautions"] = (
        DEFAULT_PRECAUTIONS
    )

    return recommendations


# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def get_confidence_level(
    score: float
) -> str:

    if score >= VERY_HIGH_CONFIDENCE:

        return "Very High"

    elif score >= HIGH_CONFIDENCE:

        return "High"

    elif score >= MEDIUM_CONFIDENCE:

        return "Moderate"

    return "Low"


# =========================================================
# GENERATE EXPLANATION
# =========================================================

def generate_similarity_reason(case):

    keywords = []

    important_fields = [

        "skin_condition",

        "affected_skin_area",

        "objective_findings",

        "symptoms",

        "chief_complaint"
    ]

    for field in important_fields:

        value = safe_text(
            case.get(field)
        )

        if value:

            keywords.append(value)

    keywords = remove_duplicates(
        keywords
    )

    if len(keywords) == 0:

        return (
            "Matched using semantic similarity retrieval"
        )

    return (
        "Matched based on: " +
        ", ".join(keywords[:3])
    )


# =========================================================
# SANITIZE MATCH
# =========================================================

def sanitize_match(
    case
) -> Dict[str, Any]:

    try:

        similarity_score = round(

            float(
                case.get(
                    "similarity",
                    0.0
                )
            ),

            4
        )

    except Exception:

        similarity_score = 0.0

    similarity_score = max(
        0.0,
        min(1.0, similarity_score)
    )

    recommendations = (
        generate_recommendations(case)
    )

    return {

        "case_id":
            str(
                case.get(
                    "case_id",
                    "Unknown"
                )
            ),

        "match_score":
            similarity_score,

        "confidence_level":
            get_confidence_level(
                similarity_score
            ),

        "skin_condition":
            safe_text(
                case.get(
                    "skin_condition",
                    "Unknown"
                )
            ),

        "affected_skin_area":
            safe_text(
                case.get(
                    "affected_skin_area",
                    "Unknown"
                )
            ),

        "symptoms":
            safe_text(
                case.get(
                    "symptoms",
                    "Unknown"
                )
            ),

        "doctor_notes":
            safe_text(
                case.get(
                    "doctor_notes",
                    "No notes available"
                )
            ),

        "matched_keywords":
            case.get(
                "matched_keywords",
                []
            ),

        "semantic_score":
            similarity_score,

        "retrieval_source":
            "BioBERT Semantic Retrieval",

        "explanation":
            generate_similarity_reason(
                case
            ),

        "recommendation":
            recommendations
    }


# =========================================================
# MAIN PIPELINE
# =========================================================

def clinical_match_pipeline(

    request,

    request_id,

    search_query="",

    generated_context="",

    combined_symptoms="",

    patient_metadata=None,

    log_event=None
):

    start_time = time.time()

    try:

        # =================================================
        # FETCH DATABASE
        # =================================================

        case_database = fetch_case_database()

        if not isinstance(
            case_database,
            list
        ):

            raise HTTPException(

                status_code=500,

                detail={

                    "status":
                        "Failed",

                    "message":
                        "Invalid database format"
                }
            )

        if len(case_database) == 0:

            raise HTTPException(

                status_code=500,

                detail={

                    "status":
                        "Failed",

                    "message":
                        "Database is empty"
                }
            )

        # =================================================
        # BUILD DYNAMIC INPUTS
        # =================================================

        if not search_query:

            search_query = build_search_query(
                request
            )

        if not generated_context:

            generated_context = (
                build_clinical_context(
                    request
                )
            )

        if not combined_symptoms:

            combined_symptoms = " ".join([

                safe_text(
                    safe_attr(
                        request,
                        "skin_condition"
                    )
                ),

                safe_text(
                    safe_attr(
                        request,
                        "symptoms"
                    )
                ),

                safe_text(
                    safe_attr(
                        request,
                        "objective_findings"
                    )
                )
            ])

        search_query = normalize_text(
            search_query
        )

        generated_context = normalize_text(
            generated_context
        )

        combined_symptoms = normalize_text(
            combined_symptoms
        )

        # =================================================
        # EMPTY QUERY CHECK
        # =================================================

        if not search_query:

            raise HTTPException(

                status_code=400,

                detail={

                    "error":
                        "Invalid Input",

                    "message":
                        "Search query is empty"
                }
            )

        logger.info(
            f"Search Query: {search_query}"
        )

        # =================================================
        # RETRIEVAL
        # =================================================

        retrieved_cases = retrieve_similar_cases(

            query_text=search_query,

            case_database=case_database,

            top_k=max(
                TOP_K,
                MAX_MATCH_RESULTS
            )
        )

        # =================================================
        # NO MATCH
        # =================================================

        if not retrieved_cases:

            return {

                "status":
                    "No Match",

                "message":
                    "No similar clinical cases found",

                "matches":
                    [],

                "total_matches_found":
                    0,

                "confidence_score":
                    0.0,

                "generated_context":
                    generated_context,

                "search_query":
                    search_query,

                "processing_time_ms":
                    round(
                        (
                            time.time() -
                            start_time
                        ) * 1000,
                        2
                    ),

                "explanation":
                    "No relevant historical cases found"
            }

        # =================================================
        # LIMIT RESULTS
        # =================================================

        top_matches = retrieved_cases[
            :MAX_MATCH_RESULTS
        ]

        # =================================================
        # FORMAT RESULTS
        # =================================================

        formatted_matches = []

        for case in top_matches:

            try:

                formatted_matches.append(
                    sanitize_match(case)
                )

            except Exception as e:

                logger.error(
                    f"Formatting Error: {str(e)}"
                )

                continue

        # =================================================
        # EMPTY FORMATTED RESULTS
        # =================================================

        if len(formatted_matches) == 0:

            raise HTTPException(

                status_code=500,

                detail={

                    "status":
                        "Failed",

                    "message":
                        "Unable to format retrieved cases"
                }
            )

        # =================================================
        # CONFIDENCE SCORE
        # =================================================

        confidence_score = round(

            sum([

                match["match_score"]

                for match in formatted_matches

            ]) / len(formatted_matches),

            4
        )

        confidence_score = max(
            0.0,
            min(1.0, confidence_score)
        )

        # =================================================
        # PROCESSING TIME
        # =================================================

        total_time = round(

            (
                time.time() -
                start_time
            ) * 1000,

            2
        )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        return {

            "status":
                "Success",

            "message":
                "Clinical matches retrieved successfully",

            "matches":
                formatted_matches,

            "total_matches_found":
                len(formatted_matches),

            "confidence_score":
                confidence_score,

            "generated_context":
                generated_context,

            "search_query":
                search_query,

            "processing_time_ms":
                total_time,

            "explanation":
                (
                    "AI-powered semantic clinical "
                    "retrieval completed successfully"
                )
        }

    # =====================================================
    # HTTP ERRORS
    # =====================================================

    except HTTPException:

        raise

    # =====================================================
    # UNKNOWN ERRORS
    # =====================================================

    except Exception as e:

        logger.error(
            traceback.format_exc()
        )

        raise HTTPException(

            status_code=500,

            detail={

                "status":
                    "Failed",

                "message":
                    "Clinical pipeline execution failed",

                "matches":
                    [],

                "confidence_score":
                    0.0,

                "explanation":
                    str(e)
            }
        )