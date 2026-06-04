from typing import List, Dict, Any
import logging
import json
import time
from collections import Counter


logger = logging.getLogger(__name__)


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)


# =========================================================
# LOG FUNCTION
# =========================================================

def log_event(
    event_type: str,
    message: str,
    extra: Dict = None
):

    log_data = {
        "event": event_type,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if extra:
        log_data.update(extra)

    logger.info(json.dumps(log_data))


# =========================================================
# SAFE VALUE HELPER
# =========================================================

def safe_string(value, default="Unknown"):

    if value in [None, "", [], {}]:
        return default

    return str(value).strip()


# =========================================================
# CONFIDENCE LABEL
# =========================================================

def get_confidence_label(score: float) -> str:

    if score >= 0.85:
        return "High"

    if score >= 0.60:
        return "Moderate"

    return "Low"


# =========================================================
# KEYWORD EXTRACTION
# =========================================================

def extract_common_keywords(
    top_matches: List[Dict]
) -> List[str]:

    keywords = []

    for case in top_matches:

        try:

            matched_keywords = case.get(
                "matched_keywords",
                []
            )

            if isinstance(matched_keywords, list):

                keywords.extend([
                    str(word).lower().strip()
                    for word in matched_keywords
                    if word
                ])

        except Exception:
            continue

    keyword_counter = Counter(keywords)

    common_keywords = [

        keyword
        for keyword, _ in keyword_counter.most_common(10)
    ]

    return common_keywords


# =========================================================
# INSIGHT AGGREGATOR
# =========================================================

class InsightAggregator:

    # =====================================================
    # MAIN AGGREGATION FUNCTION
    # =====================================================

    def aggregate_insights(
        self,
        top_matches: List[Dict],
        explanation: str,
        confidence_data: Dict
    ) -> Dict[str, Any]:

        start_time = time.time()

        log_event(
            "insight_aggregation_started",
            "Starting clinical insight aggregation",
            {
                "input_matches":
                    len(top_matches)
                    if isinstance(top_matches, list)
                    else 0
            }
        )

        # -------------------------------------------------
        # INPUT VALIDATION
        # -------------------------------------------------

        if not isinstance(top_matches, list):

            log_event(
                "validation_warning",
                "top_matches invalid"
            )

            top_matches = []

        if not isinstance(confidence_data, dict):

            log_event(
                "validation_warning",
                "confidence_data invalid"
            )

            confidence_data = {
                "confidence_score": 0.0
            }

        if not explanation:

            explanation = (
                "No explanation available."
            )

        # -------------------------------------------------
        # NO MATCH CONDITION
        # -------------------------------------------------

        if len(top_matches) == 0:

            log_event(
                "no_matches",
                "No similar clinical cases found"
            )

            return {

                "status":
                    "No Match",

                "suggested_resolution":
                    (
                        "No clinically similar "
                        "historical cases were identified. "
                        "Manual expert clinical review "
                        "is recommended."
                    ),

                "confidence_score":
                    confidence_data.get(
                        "confidence_score",
                        0.0
                    ),

                "confidence_level":
                    "Low",

                "predicted_category":
                    "Unknown",

                "recommended_tests":
                    [],

                "recommended_medicines":
                    [],

                "common_keywords":
                    [],

                "top_case_ids":
                    [],

                "top_match_summary":
                    [],

                "explanation":
                    explanation
            }

        # -------------------------------------------------
        # AGGREGATION CONTAINERS
        # -------------------------------------------------

        category_scores = {}

        test_scores = {}

        medicine_scores = {}

        similarity_scores = []

        top_case_ids = []

        processed_cases = 0

        top_match_summary = []

        # -------------------------------------------------
        # PROCESS MATCHES
        # -------------------------------------------------

        for case in top_matches:

            if not isinstance(case, dict):

                log_event(
                    "invalid_case",
                    "Skipping malformed case"
                )

                continue

            try:

                similarity = float(
                    case.get(
                        "similarity",
                        case.get(
                            "match_score",
                            0.0
                        )
                    )
                )

                similarity = max(
                    0.0,
                    min(1.0, similarity)
                )

                if similarity <= 0:
                    continue

                # -----------------------------------------
                # CATEGORY
                # -----------------------------------------

                category = safe_string(

                    case.get(
                        "category",
                        case.get(
                            "affected_body_part",
                            "Unknown"
                        )
                    )
                )

                category_scores[category] = (

                    category_scores.get(
                        category,
                        0.0
                    ) + similarity
                )

                # -----------------------------------------
                # TESTS
                # -----------------------------------------

                recommended_tests = case.get(
                    "recommended_tests",
                    []
                )

                if isinstance(
                    recommended_tests,
                    list
                ):

                    for test in recommended_tests:

                        test = safe_string(
                            test,
                            ""
                        )

                        if test:

                            test_scores[test] = (

                                test_scores.get(
                                    test,
                                    0.0
                                ) + similarity
                            )

                # -----------------------------------------
                # MEDICINES
                # -----------------------------------------

                recommended_medicines = case.get(
                    "recommended_medicines",
                    []
                )

                if isinstance(
                    recommended_medicines,
                    list
                ):

                    for medicine in recommended_medicines:

                        medicine = safe_string(
                            medicine,
                            ""
                        )

                        if medicine:

                            medicine_scores[medicine] = (

                                medicine_scores.get(
                                    medicine,
                                    0.0
                                ) + similarity
                            )

                # -----------------------------------------
                # CASE IDS
                # -----------------------------------------

                case_id = safe_string(
                    case.get(
                        "case_id",
                        "Unknown"
                    )
                )

                top_case_ids.append(
                    case_id
                )

                # -----------------------------------------
                # SIMILARITY SCORES
                # -----------------------------------------

                similarity_scores.append(
                    similarity
                )

                # -----------------------------------------
                # SUMMARY
                # -----------------------------------------

                top_match_summary.append({

                    "case_id":
                        case_id,

                    "chief_complaint":
                        safe_string(
                            case.get(
                                "chief_complaint",
                                "Unknown"
                            )
                        ),

                    "match_score":
                        round(
                            similarity,
                            4
                        ),

                    "confidence_level":
                        get_confidence_label(
                            similarity
                        )
                })

                processed_cases += 1

            except Exception as e:

                log_event(
                    "case_processing_error",
                    "Error processing clinical match",
                    {
                        "error": str(e)
                    }
                )

                continue

        # -------------------------------------------------
        # FALLBACK IF ALL CASES FAILED
        # -------------------------------------------------

        if processed_cases == 0:

            return {

                "status":
                    "Failed",

                "suggested_resolution":
                    (
                        "Clinical insight aggregation "
                        "could not process the retrieved cases."
                    ),

                "confidence_score":
                    0.0,

                "confidence_level":
                    "Low",

                "predicted_category":
                    "Unknown",

                "recommended_tests":
                    [],

                "recommended_medicines":
                    [],

                "common_keywords":
                    [],

                "top_case_ids":
                    [],

                "top_match_summary":
                    [],

                "explanation":
                    explanation
            }

        # -------------------------------------------------
        # FINAL PREDICTIONS
        # -------------------------------------------------

        predicted_category = (

            max(
                category_scores,
                key=category_scores.get
            )

            if category_scores
            else "Unknown"
        )

        predicted_tests = [

            key
            for key, _ in sorted(

                test_scores.items(),

                key=lambda x: x[1],

                reverse=True
            )[:5]
        ]

        predicted_medicines = [

            key
            for key, _ in sorted(

                medicine_scores.items(),

                key=lambda x: x[1],

                reverse=True
            )[:5]
        ]

        # -------------------------------------------------
        # COMMON KEYWORDS
        # -------------------------------------------------

        common_keywords = (
            extract_common_keywords(
                top_matches
            )
        )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        average_similarity = round(

            sum(similarity_scores) /
            len(similarity_scores),

            4
        )

        confidence_score = round(

            float(
                confidence_data.get(
                    "confidence_score",
                    average_similarity
                )
            ),

            4
        )

        confidence_level = (
            get_confidence_label(
                confidence_score
            )
        )

        # -------------------------------------------------
        # SUGGESTED RESOLUTION
        # -------------------------------------------------

        suggested_resolution = (

            f"Predicted Clinical Category: "
            f"{predicted_category}\n\n"

            f"Recommended Diagnostic Direction: "
            f"Clinical findings show strong similarity "
            f"with historical cases related to "
            f"{predicted_category.lower()} conditions.\n\n"

            f"Recommended Tests: "
            f"{', '.join(predicted_tests) if predicted_tests else 'Clinical evaluation'}\n\n"

            f"Potential Medications: "
            f"{', '.join(predicted_medicines) if predicted_medicines else 'Symptomatic management'}"
        )

        # -------------------------------------------------
        # EXECUTION TIME
        # -------------------------------------------------

        total_time = round(
            (
                time.time() -
                start_time
            ) * 1000,
            2
        )

        # -------------------------------------------------
        # FINAL LOGGING
        # -------------------------------------------------

        log_event(
            "insight_aggregation_completed",
            "Clinical insight aggregation completed",
            {
                "processed_cases":
                    processed_cases,

                "predicted_category":
                    predicted_category,

                "confidence_score":
                    confidence_score,

                "execution_time_ms":
                    total_time
            }
        )

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

        return {

            "status":
                "Success",

            "predicted_category":
                predicted_category,

            "suggested_resolution":
                suggested_resolution,

            "confidence_score":
                confidence_score,

            "confidence_level":
                confidence_level,

            "recommended_tests":
                predicted_tests,

            "recommended_medicines":
                predicted_medicines,

            "common_keywords":
                common_keywords,

            "top_case_ids":
                top_case_ids,

            "top_match_summary":
                top_match_summary,

            "average_similarity":
                average_similarity,

            "processed_cases":
                processed_cases,

            "explanation":
                explanation
        }