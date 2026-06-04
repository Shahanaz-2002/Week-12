import logging
import json
import time

from typing import List, Dict, Any


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# LOG FUNCTION
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
# SAFE FLOAT CONVERSION
# =========================================================

def safe_float(
    value,
    default=0.0
):

    try:

        return float(value)

    except Exception:

        return default


# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def get_confidence_level(
    score: float
) -> str:

    if score >= 0.85:

        return "High"

    elif score >= 0.60:

        return "Moderate"

    return "Low"


# =========================================================
# EXPLANATION GENERATOR
# =========================================================

class ExplanationGenerator:

    # =====================================================
    # GENERATE EXPLANATION
    # =====================================================

    def generate_explanation(
        self,
        retrieved_cases: List[Dict]
    ) -> str:

        start_time = time.time()

        # -------------------------------------------------
        # START LOG
        # -------------------------------------------------

        log_event(
            "explanation_start",
            "Generating clinical explanation",
            {
                "num_cases":
                    len(retrieved_cases)
                    if isinstance(
                        retrieved_cases,
                        list
                    )
                    else 0
            }
        )

        try:

            # =================================================
            # INPUT VALIDATION
            # =================================================

            if not isinstance(
                retrieved_cases,
                list
            ):

                log_event(
                    "validation_warning",
                    "retrieved_cases is not a list"
                )

                return (
                    "Explanation could not "
                    "be generated due to "
                    "invalid retrieval data."
                )

            # =================================================
            # NO CASES FOUND
            # =================================================

            if len(retrieved_cases) == 0:

                log_event(
                    "no_cases",
                    "No retrieved cases available"
                )

                return (

                    "Clinical Analysis Summary:\n\n"

                    "- No similar historical "
                    "clinical cases were found.\n"

                    "- Semantic similarity "
                    "retrieval returned "
                    "insufficient matching data.\n\n"

                    "Recommendation:\n"

                    "- Proceed with manual "
                    "clinical evaluation.\n"

                    "- Consider collecting "
                    "additional patient details "
                    "for improved retrieval."
                )

            # =================================================
            # TOTAL CASE COUNT
            # =================================================

            case_count = len(
                retrieved_cases
            )

            # =================================================
            # EXTRACT SIMILARITY SCORES
            # =================================================

            similarities = []

            for case in retrieved_cases:

                try:

                    score = safe_float(

                        case.get(
                            "similarity",

                            case.get(
                                "match_score",
                                0.0
                            )
                        )
                    )

                    score = max(
                        0.0,
                        min(score, 1.0)
                    )

                    if score > 0:

                        similarities.append(
                            score
                        )

                except Exception:

                    log_event(
                        "similarity_error",
                        "Invalid similarity skipped"
                    )

                    continue

            # =================================================
            # AVERAGE SIMILARITY
            # =================================================

            if similarities:

                avg_similarity = round(

                    (
                        sum(similarities)
                        / len(similarities)
                    ) * 100,

                    2
                )

            else:

                avg_similarity = 0.0

            # =================================================
            # TOP MATCH
            # =================================================

            top_case = retrieved_cases[0]

            # -------------------------------------------------
            # TOP SCORE
            # -------------------------------------------------

            top_score = round(

                safe_float(

                    top_case.get(
                        "similarity",

                        top_case.get(
                            "match_score",
                            0.0
                        )
                    )
                ) * 100,

                2
            )

            # -------------------------------------------------
            # CONFIDENCE LEVEL
            # -------------------------------------------------

            confidence_level = (
                get_confidence_level(
                    top_score / 100
                )
            )

            # -------------------------------------------------
            # CASE INFORMATION
            # -------------------------------------------------

            category = top_case.get(
                "category",
                "General Clinical"
            )

            chief_complaint = top_case.get(
                "chief_complaint",
                "Unknown"
            )

            body_part = top_case.get(
                "affected_body_part",
                "Unknown"
            )

            resolution_notes = top_case.get(
                "resolution_notes",

                top_case.get(
                    "doctor_notes",
                    "No standard resolution available"
                )
            )

            matched_keywords = top_case.get(
                "matched_keywords",
                []
            )

            # =================================================
            # MATCHED KEYWORDS TEXT
            # =================================================

            if (
                isinstance(
                    matched_keywords,
                    list
                )
                and len(
                    matched_keywords
                ) > 0
            ):

                keyword_text = ", ".join(

                    matched_keywords[:5]
                )

            else:

                keyword_text = (
                    "No major keywords identified"
                )

            # =================================================
            # BUILD EXPLANATION
            # =================================================

            explanation = (

                "Clinical Similarity Analysis\n\n"

                "Summary:\n"

                f"- Retrieved "
                f"{case_count} "
                f"similar clinical case(s).\n"

                f"- Top similarity score: "
                f"{top_score:.1f}%\n"

                f"- Average similarity score: "
                f"{avg_similarity:.1f}%\n"

                f"- Confidence level: "
                f"{confidence_level}\n\n"

                "Top Match Details:\n"

                f"- Clinical category: "
                f"{category}\n"

                f"- Chief complaint: "
                f"{chief_complaint}\n"

                f"- Affected body part: "
                f"{body_part}\n"

                f"- Matched keywords: "
                f"{keyword_text}\n\n"

                "Clinical Insight:\n"

                f"- Historical records show "
                f"similar symptom patterns "
                f"and clinical findings.\n"

                f"- Suggested management "
                f"approach: "
                f"{resolution_notes}\n\n"

                "Conclusion:\n"

                "- The recommendation was "
                "generated using AI-powered "
                "semantic similarity retrieval "
                "from historical clinical cases."
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
            # SUCCESS LOG
            # =================================================

            log_event(
                "explanation_generated",
                "Clinical explanation generated successfully",
                {
                    "top_similarity":
                        top_score,

                    "average_similarity":
                        avg_similarity,

                    "confidence_level":
                        confidence_level,

                    "processing_time_ms":
                        total_time
                }
            )

            return explanation

        # =====================================================
        # GLOBAL ERROR HANDLING
        # =====================================================

        except Exception as e:

            log_event(
                "explanation_error",
                "Error generating explanation",
                {
                    "error": str(e)
                }
            )

            return (

                "Clinical explanation "
                "could not be generated "
                "due to an internal "
                "processing error."
            )


# =========================================================
# GLOBAL EXPLANATION ENGINE INSTANCE
# =========================================================

explanation_generator = ExplanationGenerator()