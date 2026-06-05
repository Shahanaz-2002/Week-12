# =========================================================
# services/analyze_service.py
# =========================================================

import time
import traceback
import re
import logging

from typing import Dict, List, Any

from fastapi import HTTPException

from retrieval.retrieval_engine import retrieve_similar_cases
from retrieval.database import fetch_case_database

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
        normalized = normalize_text(value).lower()
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
        safe_attr(request, "chief_complaint"),
        safe_attr(request, "affected_body_part"),
    ]

    for field in weighted_fields:
        cleaned = normalize_text(field)
        if cleaned:
            query_parts.append(cleaned)

    query_parts = remove_duplicates(query_parts)
    return " | ".join(query_parts).strip()

# =========================================================
# BUILD CONTEXT
# =========================================================

def build_clinical_context(request) -> str:
    field_mapping = {
        "Age": safe_attr(request, "age"),
        "Gender": safe_attr(request, "gender"),
        "Occupation": safe_attr(request, "occupation"),
        "Skin Type": safe_attr(request, "skin_type"),
        "Skin Condition": safe_attr(request, "skin_condition"),
        "Affected Skin Area": safe_attr(request, "affected_skin_area"),
        "Symptoms": safe_attr(request, "symptoms"),
        "Symptoms Duration": safe_attr(request, "symptoms_duration"),
        "Previous Skin Conditions": safe_attr(request, "previous_skin_conditions"),
        "Allergies": safe_attr(request, "allergies"),
        "Doctor Notes": safe_attr(request, "doctor_notes"),
        "Clinical History": safe_attr(request, "clinical_history"),
        "Chief Complaint": safe_attr(request, "chief_complaint"),
        "Affected Body Part": safe_attr(request, "affected_body_part"),
    }

    context_parts = []

    for field_name, value in field_mapping.items():
        cleaned = normalize_text(value)
        if cleaned:
            context_parts.append(f"{field_name}: {cleaned}")

    return "\n".join(context_parts)

# =========================================================
# RECOMMENDATIONS ENGINE
# =========================================================

def generate_recommendations(case) -> Dict[str, List[str]]:
    recommendations = {
        "recommended_tests": [],
        "recommended_medicines": [],
        "skincare_plan": [],
        "precautions": []
    }

    combined_text = (
        safe_text(case.get("skin_condition")) + " " +
        safe_text(case.get("symptoms")) + " " +
        safe_text(case.get("doctor_notes"))
    ).lower()

    if "acne" in combined_text:
        recommendations["recommended_tests"] = ["Dermatoscopy", "Hormonal Evaluation"]
        recommendations["recommended_medicines"] = ["Benzoyl Peroxide", "Topical Retinoid"]

    elif "eczema" in combined_text:
        recommendations["recommended_tests"] = ["Patch Allergy Test"]
        recommendations["recommended_medicines"] = ["Topical Corticosteroid", "Moisturizer"]

    elif "psoriasis" in combined_text:
        recommendations["recommended_tests"] = ["Skin Biopsy"]
        recommendations["recommended_medicines"] = ["Topical Steroids"]

    elif "fungal" in combined_text or "tinea" in combined_text:
        recommendations["recommended_tests"] = ["KOH Examination"]
        recommendations["recommended_medicines"] = ["Clotrimazole", "Ketoconazole"]

    else:
        recommendations["recommended_tests"] = DEFAULT_RECOMMENDED_TESTS
        recommendations["recommended_medicines"] = DEFAULT_RECOMMENDED_MEDICINES

    recommendations["skincare_plan"] = DEFAULT_SKINCARE_PLAN
    recommendations["precautions"] = DEFAULT_PRECAUTIONS

    return recommendations

# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def get_confidence_level(score: float) -> str:
    if score >= VERY_HIGH_CONFIDENCE:
        return "Very High"
    elif score >= HIGH_CONFIDENCE:
        return "High"
    elif score >= MEDIUM_CONFIDENCE:
        return "Moderate"
    return "Low"

# =========================================================
# SANITIZE MATCH
# =========================================================

def sanitize_match(case) -> Dict[str, Any]:
    try:
        similarity_score = round(float(case.get("similarity", 0.0)), 4)
    except Exception:
        similarity_score = 0.0

    similarity_score = max(0.0, min(1.0, similarity_score))

    return {
        "case_id": str(case.get("case_id", "Unknown")),
        "match_score": similarity_score,
        "confidence_level": get_confidence_level(similarity_score),
        "skin_condition": safe_text(case.get("skin_condition", "Unknown")),
        "affected_skin_area": safe_text(case.get("affected_skin_area", "Unknown")),
        "symptoms": safe_text(case.get("symptoms", "Unknown")),
        "doctor_notes": safe_text(case.get("doctor_notes", "No notes available")),
        "matched_keywords": case.get("matched_keywords", []),
        "semantic_score": similarity_score,
        "retrieval_source": "BioBERT Semantic Retrieval",
        "explanation": generate_similarity_reason(case),
        "recommendation": generate_recommendations(case)
    }

# =========================================================
# EXPLANATION
# =========================================================

def generate_similarity_reason(case):
    keywords = []

    for field in ["skin_condition", "affected_skin_area", "objective_findings", "symptoms", "chief_complaint"]:
        value = safe_text(case.get(field))
        if value:
            keywords.append(value)

    keywords = remove_duplicates(keywords)

    if not keywords:
        return "Matched using semantic similarity retrieval"

    return "Matched based on: " + ", ".join(keywords[:3])

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
        case_database = fetch_case_database()

        if not isinstance(case_database, list):
            raise HTTPException(500, {"message": "Invalid database format"})

        if len(case_database) == 0:
            raise HTTPException(500, {"message": "Database is empty"})

        if not search_query:
            search_query = build_search_query(request)

        if not generated_context:
            generated_context = build_clinical_context(request)

        if not combined_symptoms:
            combined_symptoms = " ".join([
                safe_text(safe_attr(request, "skin_condition")),
                safe_text(safe_attr(request, "symptoms")),
                safe_text(safe_attr(request, "objective_findings"))
            ])

        search_query = normalize_text(search_query)

        if not search_query:
            raise HTTPException(400, {"message": "Search query is empty"})

        retrieved_cases = retrieve_similar_cases(
            query_text=search_query,
            case_database=case_database,
            top_k=max(TOP_K, MAX_MATCH_RESULTS)
        )

        if not retrieved_cases:
            return {
                "status": "No Match",
                "matches": [],
                "confidence_score": 0.0,
                "search_query": search_query,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        top_matches = retrieved_cases[:MAX_MATCH_RESULTS]
        formatted_matches = [sanitize_match(c) for c in top_matches]

        confidence_score = round(
            sum(m["match_score"] for m in formatted_matches) / len(formatted_matches),
            4
        )

        return {
            "status": "Success",
            "matches": formatted_matches,
            "total_matches_found": len(formatted_matches),
            "confidence_score": max(0.0, min(1.0, confidence_score)),
            "search_query": search_query,
            "generated_context": generated_context,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, {"message": str(e)})



# =========================================================
# IMPROVED SIMILAR CASES PIPELINE
# =========================================================

def similar_cases_pipeline(request):

    try:

        # =====================================================
        # BUILD SEARCH QUERY
        # =====================================================

        query_parts = []

        symptoms = getattr(request, "symptoms", [])

        if symptoms:
            query_parts.extend(
                [normalize_text(str(symptom))
                 for symptom in symptoms
                 if safe_text(symptom)]
            )

        assessment_notes = safe_text(
            getattr(request, "assessment_notes", "")
        )

        diagnosis = safe_text(
            getattr(request, "diagnosis", "")
        )

        if assessment_notes:
            query_parts.append(normalize_text(assessment_notes))

        if diagnosis:
            query_parts.append(normalize_text(diagnosis))

        query_parts = remove_duplicates(query_parts)

        search_query = " | ".join(query_parts).strip()

        # =====================================================
        # VALIDATE QUERY
        # =====================================================

        if not search_query:

            raise HTTPException(
                status_code=400,
                detail="At least one symptom, assessment note, or diagnosis is required"
            )

        logger.info(
            f"[SIMILAR_CASES] Search Query: {search_query}"
        )

        # =====================================================
        # LOAD DATABASE
        # =====================================================

        case_database = fetch_case_database()

        if not isinstance(case_database, list):

            raise HTTPException(
                status_code=500,
                detail="Invalid clinical database format"
            )

        if len(case_database) == 0:

            return {
                "similar_cases": [],
                "similarity_score": []
            }

        # =====================================================
        # RETRIEVE MATCHES
        # =====================================================

        retrieved_cases = retrieve_similar_cases(
            query_text=search_query,
            case_database=case_database,
            top_k=MAX_MATCH_RESULTS
        )

        if not retrieved_cases:

            return {
                "similar_cases": [],
                "similarity_score": []
            }

        # =====================================================
        # SORT BY SIMILARITY
        # =====================================================

        retrieved_cases = sorted(
            retrieved_cases,
            key=lambda x: float(x.get("similarity", 0.0)),
            reverse=True
        )

        # =====================================================
        # FORMAT RESPONSE
        # =====================================================

        similar_cases = []
        similarity_score = []

        for case in retrieved_cases[:MAX_MATCH_RESULTS]:

            try:
                score = round(
                    max(
                        0.0,
                        min(
                            1.0,
                            float(case.get("similarity", 0.0))
                        )
                    ),
                    4
                )

            except Exception:
                score = 0.0

            formatted_case = {
                "case_id": str(
                    case.get("case_id", "Unknown")
                ),

                "diagnosis": safe_text(
                    case.get("diagnosis")
                ),

                "symptoms": safe_text(
                    case.get("symptoms")
                ),

                "assessment_notes": safe_text(
                    case.get("assessment_notes")
                ),

                "doctor_notes": safe_text(
                    case.get("doctor_notes")
                ),

                "confidence_level": get_confidence_level(score)
            }

            similar_cases.append(formatted_case)
            similarity_score.append(score)

        logger.info(
            f"[SIMILAR_CASES] Retrieved {len(similar_cases)} matches"
        )

        return {
            "similar_cases": similar_cases,
            "similarity_score": similarity_score
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Similar Cases Pipeline Error: {str(e)}"
        )

        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve similar cases: {str(e)}"
        )