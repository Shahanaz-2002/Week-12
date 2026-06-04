# =========================================================
# IMPORTS
# =========================================================

from typing import List, Dict, Any

import numpy as np

import logging

import json

import time

import re

import traceback


from retrieval.embedding import BioBERTEmbedding


# =========================================================
# CONFIGURATION
# =========================================================

MIN_SIMILARITY_THRESHOLD = 0.20

MAX_KEYWORD_BOOST = 0.10

MAX_KEYWORDS_RETURN = 10


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

logging.basicConfig(

    level=logging.INFO,

    format="%(message)s",

    force=True
)

logger = logging.getLogger(__name__)


# =========================================================
# LOGGING HELPER
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

    logger.info(
        json.dumps(log_data)
    )


# =========================================================
# SAFE EMBEDDER INITIALIZATION
# =========================================================

try:

    embedder = BioBERTEmbedding()

    log_event(
        "embedder_initialized",
        "BioBERT embedder initialized successfully"
    )

except Exception as e:

    embedder = None

    log_event(
        "embedder_initialization_failed",
        "Failed to initialize BioBERT embedder",
        {
            "error": str(e)
        }
    )


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(
    text: Any
) -> str:

    if text is None:

        return ""

    text = str(text)

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(
    text: str
) -> str:

    return clean_text(
        text
    ).lower()


# =========================================================
# REMOVE DUPLICATE WORDS
# =========================================================

def remove_duplicate_words(
    text: str
) -> str:

    words = text.split()

    unique_words = []

    seen = set()

    for word in words:

        if word not in seen:

            seen.add(word)

            unique_words.append(word)

    return " ".join(
        unique_words
    )


# =========================================================
# QUERY ENHANCEMENT
# =========================================================

def enhance_query(
    query_text: str
) -> str:

    query_text = clean_text(
        query_text
    )

    medical_keywords = [

        "pain",
        "swelling",
        "injury",
        "fracture",
        "stiffness",
        "inflammation",
        "weakness",
        "mobility",
        "muscle",
        "joint",
        "tenderness",
        "sprain",
        "posture",
        "movement",
        "arthritis",
        "back",
        "knee",
        "shoulder",
        "neck",
        "hip",
        "elbow",
        "ankle",
        "spine",
        "nerve",
        "ligament",
        "tear"
    ]

    detected_keywords = []

    lower_query = query_text.lower()

    for keyword in medical_keywords:

        if keyword in lower_query:

            detected_keywords.append(
                keyword
            )

    detected_keywords = list(
        set(detected_keywords)
    )

    if detected_keywords:

        query_text += (

            " | " +

            " ".join(
                detected_keywords
            )
        )

    query_text = remove_duplicate_words(
        query_text
    )

    return query_text.strip()


# =========================================================
# COSINE SIMILARITY
# =========================================================

def cosine_similarity(

    a: np.ndarray,

    b: np.ndarray

) -> float:

    try:

        if a.size == 0 or b.size == 0:

            return 0.0

        norm_a = np.linalg.norm(a)

        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:

            return 0.0

        similarity = np.dot(
            a,
            b
        ) / (
            norm_a * norm_b
        )

        similarity = float(similarity)

        similarity = np.clip(
            similarity,
            0.0,
            1.0
        )

        return similarity

    except Exception as e:

        log_event(
            "cosine_similarity_error",
            "Cosine similarity calculation failed",
            {
                "error": str(e)
            }
        )

        return 0.0


# =========================================================
# NORMALIZE EMBEDDING
# =========================================================

def normalize_embedding(
    embedding
) -> np.ndarray:

    try:

        embedding = np.array(
            embedding,
            dtype=np.float32
        )

        if embedding.size == 0:

            return embedding

        norm = np.linalg.norm(
            embedding
        )

        if norm == 0:

            return embedding

        return embedding / norm

    except Exception:

        return np.array(
            [],
            dtype=np.float32
        )


# =========================================================
# BUILD SEARCHABLE TEXT
# =========================================================

def build_case_search_text(
    case_data: Dict
) -> str:

    text_parts = []

    searchable_fields = [

        "chief_complaint",
        "affected_body_part",
        "symptoms",
        "subjective_assessment",
        "functional_assessment",
        "physical_examination",
        "objective_findings",
        "doctor_notes",
        "clinical_history",
        "case_description",
        "previous_injuries",
        "symptoms_duration",
        "patient_pain_classification"
    ]

    for field in searchable_fields:

        value = case_data.get(
            field,
            ""
        )

        cleaned = clean_text(value)

        if cleaned:

            text_parts.append(
                cleaned
            )

    return " | ".join(
        text_parts
    )


# =========================================================
# EXTRACT MATCHED KEYWORDS
# =========================================================

def extract_matched_keywords(

    query_text: str,

    searchable_text: str

) -> List[str]:

    query_words = set(

        normalize_text(
            query_text
        ).split()
    )

    searchable_words = set(

        normalize_text(
            searchable_text
        ).split()
    )

    matched = list(

        query_words.intersection(
            searchable_words
        )
    )

    matched = [

        word.strip(
            ".,!?;:()[]{}"
        )

        for word in matched

        if len(word) > 3
    ]

    matched = list(
        set(matched)
    )

    return matched[
        :MAX_KEYWORDS_RETURN
    ]


# =========================================================
# KEYWORD BOOSTING
# =========================================================

def apply_keyword_boost(

    similarity_score: float,

    matched_keywords: List[str]

) -> float:

    boost = min(

        MAX_KEYWORD_BOOST,

        len(matched_keywords) * 0.01
    )

    boosted_score = similarity_score + boost

    return min(
        boosted_score,
        1.0
    )


# =========================================================
# CONFIDENCE LEVEL
# =========================================================

def get_confidence_level(
    score: float
) -> str:

    if score >= 0.85:

        return "High"

    if score >= 0.60:

        return "Moderate"

    return "Low"


# =========================================================
# SAFE CASE VALUE ACCESS
# =========================================================

def safe_case_value(

    case_data: Dict,

    field: str,

    default="Unknown"
):

    value = case_data.get(
        field,
        default
    )

    if value in [None, ""]:

        return default

    return value


# =========================================================
# VALIDATE CASE RECORD
# =========================================================

def validate_case_record(
    case_data
) -> bool:

    if not isinstance(
        case_data,
        dict
    ):

        return False

    embedding = case_data.get(
        "embedding"
    )

    if embedding is None:

        return False

    if len(embedding) == 0:

        return False

    return True


# =========================================================
# SAFE EMBEDDING GENERATION
# =========================================================

def generate_query_embedding(
    query_text: str
):

    if embedder is None:

        log_event(
            "embedding_error",
            "Embedding model unavailable"
        )

        return None

    try:

        # =============================================
        # FIXED METHOD NAME
        # =============================================

        embedding = embedder.generate_embedding(
            query_text
        )

        if embedding is None:

            return None

        embedding = normalize_embedding(
            embedding
        )

        if embedding.size == 0:

            return None

        return embedding

    except Exception as e:

        log_event(
            "embedding_generation_error",
            "Failed to generate embedding",
            {
                "error": str(e)
            }
        )

        return None


# =========================================================
# BUILD RESULT OBJECT
# =========================================================

def build_result_object(

    case_data: Dict,

    similarity_score: float,

    boosted_score: float,

    matched_keywords: List[str],

    searchable_text: str

) -> Dict:

    return {

        "case_id":
            safe_case_value(
                case_data,
                "case_id"
            ),

        "similarity":
            round(
                boosted_score,
                4
            ),

        "semantic_score":
            round(
                similarity_score,
                4
            ),

        "chief_complaint":
            safe_case_value(
                case_data,
                "chief_complaint"
            ),

        "affected_body_part":
            safe_case_value(
                case_data,
                "affected_body_part"
            ),

        "symptoms_duration":
            safe_case_value(
                case_data,
                "symptoms_duration"
            ),

        "doctor_notes":
            safe_case_value(
                case_data,
                "doctor_notes",
                "No notes available"
            ),

        "clinical_history":
            safe_case_value(
                case_data,
                "clinical_history",
                ""
            ),

        "objective_findings":
            safe_case_value(
                case_data,
                "objective_findings",
                ""
            ),

        "recommended_tests":
            case_data.get(
                "recommended_tests",
                []
            ),

        "recommended_medicines":
            case_data.get(
                "recommended_medicines",
                []
            ),

        "matched_keywords":
            matched_keywords,

        "confidence_level":
            get_confidence_level(
                boosted_score
            ),

        "retrieval_source":
            "BioBERT Semantic Retrieval",

        "searchable_text":
            searchable_text
    }


# =========================================================
# MAIN RETRIEVAL FUNCTION
# =========================================================

def retrieve_similar_cases(

    query_text: str,

    case_database: List[Dict],

    top_k: int = 2

) -> List[Dict]:

    start_time = time.time()

    log_event(
        "retrieval_started",
        "Clinical similarity retrieval started"
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    if not isinstance(
        query_text,
        str
    ):

        return []

    query_text = clean_text(
        query_text
    )

    if not query_text:

        return []

    if not isinstance(
        case_database,
        list
    ):

        return []

    if len(case_database) == 0:

        return []

    if not isinstance(
        top_k,
        int
    ):

        top_k = 2

    top_k = max(top_k, 1)

    # =====================================================
    # ENHANCE QUERY
    # =====================================================

    enhanced_query = enhance_query(
        query_text
    )

    # =====================================================
    # QUERY EMBEDDING
    # =====================================================

    query_embedding = generate_query_embedding(
        enhanced_query
    )

    if query_embedding is None:

        return []

    # =====================================================
    # RETRIEVAL LOOP
    # =====================================================

    results = []

    for case_data in case_database:

        try:

            if not validate_case_record(
                case_data
            ):

                continue

            case_embedding = normalize_embedding(

                case_data.get(
                    "embedding",
                    []
                )
            )

            if case_embedding.size == 0:

                continue

            if len(query_embedding) != len(case_embedding):

                continue

            similarity_score = cosine_similarity(

                query_embedding,

                case_embedding
            )

            searchable_text = (

                build_case_search_text(
                    case_data
                )
            )

            matched_keywords = (

                extract_matched_keywords(

                    enhanced_query,

                    searchable_text
                )
            )

            boosted_score = apply_keyword_boost(

                similarity_score,

                matched_keywords
            )

            if boosted_score < MIN_SIMILARITY_THRESHOLD:

                continue

            result_object = build_result_object(

                case_data,

                similarity_score,

                boosted_score,

                matched_keywords,

                searchable_text
            )

            results.append(
                result_object
            )

        except Exception as e:

            log_event(
                "case_processing_error",
                "Case processing failed",
                {
                    "error": str(e),
                    "traceback":
                        traceback.format_exc()
                }
            )

            continue

    # =====================================================
    # SORT RESULTS
    # =====================================================

    results = sorted(

        results,

        key=lambda x:
            x["similarity"],

        reverse=True
    )

    top_results = results[:top_k]

    # =====================================================
    # FINAL LOGGING
    # =====================================================

    total_time = round(

        (
            time.time() -
            start_time
        ) * 1000,

        2
    )

    log_event(
        "retrieval_completed",
        "Clinical retrieval completed successfully",
        {
            "returned_cases":
                len(top_results),

            "total_time_ms":
                total_time
        }
    )

    return top_results