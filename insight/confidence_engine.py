from config import TOP_K

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
    event_type: str,
    message: str,
    extra: Dict[str, Any] = None
):

    log_data = {

        "event": event_type,

        "message": message,

        "timestamp":
            time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if extra:

        log_data.update(extra)

    logger.info(json.dumps(log_data))


# =========================================================
# SAFE FLOAT CONVERTER
# =========================================================

def safe_float(value, default=0.0):

    try:

        return float(value)

    except Exception:

        return default


# =========================================================
# CONFIDENCE LEVEL GENERATOR
# =========================================================

def get_confidence_level(score: float) -> str:

    if score >= 0.85:

        return "High"

    elif score >= 0.60:

        return "Moderate"

    return "Low"


# =========================================================
# CONFIDENCE ENGINE
# =========================================================

class ConfidenceEngine:

    # =====================================================
    # COMPUTE CONFIDENCE
    # =====================================================

    def compute_confidence(
        self,
        retrieved_cases: List[Dict]
    ) -> Dict[str, Any]:

        start_time = time.time()

        # -------------------------------------------------
        # START LOG
        # -------------------------------------------------

        log_event(
            "confidence_start",
            "Starting confidence computation",
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

                return {

                    "confidence_score": 0.0,

                    "confidence_level": "Low",

                    "average_similarity": 0.0,

                    "support_ratio": 0.0,

                    "retrieved_cases": 0,

                    "processing_time_ms": 0.0
                }

            # =================================================
            # EMPTY CASES
            # =================================================

            if len(retrieved_cases) == 0:

                log_event(
                    "no_cases",
                    "No cases provided for confidence calculation"
                )

                return {

                    "confidence_score": 0.0,

                    "confidence_level": "Low",

                    "average_similarity": 0.0,

                    "support_ratio": 0.0,

                    "retrieved_cases": 0,

                    "processing_time_ms": 0.0
                }

            # =================================================
            # EXTRACT VALID SIMILARITIES
            # =================================================

            similarities = []

            valid_cases = 0

            for case in retrieved_cases:

                try:

                    if not isinstance(case, dict):

                        continue

                    similarity = safe_float(

                        case.get(
                            "similarity",
                            case.get(
                                "match_score",
                                0.0
                            )
                        )
                    )

                    # -----------------------------------------
                    # VALID RANGE CHECK
                    # -----------------------------------------

                    similarity = max(
                        0.0,
                        min(
                            similarity,
                            1.0
                        )
                    )

                    if similarity > 0:

                        similarities.append(
                            similarity
                        )

                        valid_cases += 1

                except Exception as e:

                    log_event(
                        "similarity_error",
                        "Invalid similarity value skipped",
                        {
                            "error": str(e)
                        }
                    )

                    continue

            # =================================================
            # NO VALID SIMILARITIES
            # =================================================

            if len(similarities) == 0:

                log_event(
                    "no_valid_similarity",
                    "No valid similarity scores found"
                )

                return {

                    "confidence_score": 0.0,

                    "confidence_level": "Low",

                    "average_similarity": 0.0,

                    "support_ratio": 0.0,

                    "retrieved_cases": 0,

                    "processing_time_ms": 0.0
                }

            # =================================================
            # AVERAGE SIMILARITY
            # =================================================

            avg_similarity = round(

                sum(similarities)
                / len(similarities),

                4
            )

            # =================================================
            # SUPPORT RATIO
            # =================================================

            if (
                isinstance(TOP_K, int)
                and TOP_K > 0
            ):

                support_ratio = round(

                    valid_cases / TOP_K,

                    4
                )

            else:

                support_ratio = 0.0

            # =================================================
            # CONFIDENCE COMPUTATION
            # =================================================

            confidence_score = (

                (0.75 * avg_similarity)

                +

                (0.25 * support_ratio)
            )

            # =================================================
            # SCORE NORMALIZATION
            # =================================================

            confidence_score = round(

                max(
                    0.0,
                    min(
                        confidence_score,
                        1.0
                    )
                ),

                4
            )

            # =================================================
            # CONFIDENCE LEVEL
            # =================================================

            confidence_level = (
                get_confidence_level(
                    confidence_score
                )
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
                "confidence_computed",
                "Confidence score calculated successfully",
                {

                    "average_similarity":
                        avg_similarity,

                    "support_ratio":
                        support_ratio,

                    "confidence_score":
                        confidence_score,

                    "confidence_level":
                        confidence_level,

                    "valid_cases":
                        valid_cases,

                    "processing_time_ms":
                        total_time
                }
            )

            # =================================================
            # FINAL RESPONSE
            # =================================================

            return {

                "confidence_score":
                    confidence_score,

                "confidence_level":
                    confidence_level,

                "average_similarity":
                    avg_similarity,

                "support_ratio":
                    support_ratio,

                "retrieved_cases":
                    valid_cases,

                "processing_time_ms":
                    total_time
            }

        # =====================================================
        # GLOBAL ERROR HANDLING
        # =====================================================

        except Exception as e:

            total_time = round(

                (
                    time.time() -
                    start_time
                ) * 1000,

                2
            )

            log_event(
                "confidence_error",
                "Error during confidence computation",
                {
                    "error": str(e),
                    "processing_time_ms": total_time
                }
            )

            return {

                "confidence_score": 0.0,

                "confidence_level": "Low",

                "average_similarity": 0.0,

                "support_ratio": 0.0,

                "retrieved_cases": 0,

                "processing_time_ms": total_time
            }


# =========================================================
# GLOBAL ENGINE INSTANCE
# =========================================================

confidence_engine = ConfidenceEngine()