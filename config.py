# =========================================================
# config.py
# =========================================================

import os
import torch


# =========================================================
# ENVIRONMENT
# =========================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).lower()


# =========================================================
# PROJECT ROOT
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# MONGODB CONFIGURATION
# =========================================================
# IMPORTANT:
# CHANGED TO YOUR ACTUAL DATABASE
# clinical_match1000_db
# patient_cases
# =========================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "clinical_match1000_db"
)

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "patient_cases"
)


# =========================================================
# DATABASE TIMEOUTS
# =========================================================

MONGO_SERVER_SELECTION_TIMEOUT_MS = 5000

MONGO_CONNECT_TIMEOUT_MS = 5000

MONGO_SOCKET_TIMEOUT_MS = 5000

MONGO_MAX_POOL_SIZE = 10

MONGO_MIN_POOL_SIZE = 1


# =========================================================
# RETRIEVAL CONFIGURATION
# =========================================================

TOP_K = 2

DEFAULT_TOP_K = 2

MAX_MATCH_RESULTS = 2

MIN_SIMILARITY_SCORE = 0.20

DEFAULT_SIMILARITY_THRESHOLD = 0.20

ENABLE_LOW_SCORE_FILTER = True

LOW_SCORE_FILTER_THRESHOLD = 0.20


# =========================================================
# EMBEDDING CONFIGURATION
# =========================================================
# IMPORTANT:
# SAME MODEL MUST BE USED IN:
# - embedding.py
# - embedding_store.py
# - retrieval_engine.py
# =========================================================

EMBEDDING_MODEL_NAME = (
    "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb"
)

DEFAULT_EMBEDDING_MODEL = EMBEDDING_MODEL_NAME

EMBEDDING_DIM = 768

EMBEDDING_VERSION = "biobert_semantic_v2"

BATCH_SIZE = 16

NORMALIZE_EMBEDDINGS = True

ENABLE_EMBEDDING_CACHE = True

EMBEDDING_CACHE_SIZE = 1000


# =========================================================
# DEVICE CONFIGURATION
# =========================================================

USE_GPU = torch.cuda.is_available()

DEVICE = (
    "cuda"
    if USE_GPU
    else "cpu"
)


# =========================================================
# KEYWORD BOOST CONFIGURATION
# =========================================================

ENABLE_KEYWORD_BOOST = True

KEYWORD_BOOST_FACTOR = 0.01

MAX_KEYWORD_BOOST = 0.10


# =========================================================
# API CONFIGURATION
# =========================================================

API_TITLE = (
    "AI Clinical Match API"
)

API_DESCRIPTION = (
    "AI-powered semantic clinical retrieval "
    "using BioBERT embeddings"
)

API_VERSION = "6.0.0"

API_HOST = "0.0.0.0"

API_PORT = 8000

REQUEST_TIMEOUT_SECONDS = 30


# =========================================================
# INPUT LIMITS
# =========================================================

MAX_TEXT_INPUT_LENGTH = 2000

MAX_QUERY_LENGTH = 2000

MAX_CONTEXT_LENGTH = 5000

MAX_FIELD_LENGTH = 1000


# =========================================================
# CONFIDENCE THRESHOLDS
# =========================================================

VERY_HIGH_CONFIDENCE = 0.90

HIGH_CONFIDENCE = 0.75

MEDIUM_CONFIDENCE = 0.55

LOW_CONFIDENCE = 0.30


# =========================================================
# RESPONSE CONFIGURATION
# =========================================================

INCLUDE_SEARCHABLE_TEXT = False

INCLUDE_EMBEDDINGS_IN_RESPONSE = False

ENABLE_EXPLANATION_GENERATION = True

ENABLE_RECOMMENDATIONS = True


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

LOG_LEVEL = "INFO"

ENABLE_JSON_LOGGING = True

LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# =========================================================
# SUPPORTED CONDITIONS
# =========================================================

SUPPORTED_DERMATOLOGY_CONDITIONS = [

    "Acne",

    "Eczema",

    "Psoriasis",

    "Fungal Infection",

    "Dermatitis",

    "Rosacea",

    "Vitiligo",

    "Melasma",

    "Skin Allergy",

    "Urticaria",

    "Seborrheic Dermatitis",

    "Folliculitis",

    "Hyperpigmentation",

    "Tinea",

    "Scabies"
]


# =========================================================
# SUPPORTED SKIN TYPES
# =========================================================

SUPPORTED_SKIN_TYPES = [

    "Oily",

    "Dry",

    "Combination",

    "Sensitive",

    "Normal"
]


# =========================================================
# DEFAULT RECOMMENDATIONS
# =========================================================

DEFAULT_RECOMMENDED_TESTS = [

    "Clinical Examination"
]

DEFAULT_RECOMMENDED_MEDICINES = [

    "Symptomatic Treatment"
]

DEFAULT_SKINCARE_PLAN = [

    "Use gentle cleanser",

    "Apply moisturizer regularly",

    "Use sunscreen daily"
]

DEFAULT_PRECAUTIONS = [

    "Avoid harsh chemicals",

    "Maintain proper hygiene"
]


# =========================================================
# SECURITY SETTINGS
# =========================================================

ALLOWED_GENDERS = [

    "Male",

    "Female",

    "Other",

    "Prefer Not To Say"
]


# =========================================================
# DEBUG MODE
# =========================================================

DEBUG_MODE = (
    ENVIRONMENT == "development"
)


# =========================================================
# DEFAULT SEARCHABLE FIELDS
# =========================================================

SEARCHABLE_FIELDS = [

    "chief_complaint",

    "affected_body_part",

    "symptoms",

    "doctor_notes",

    "clinical_history",

    "objective_findings",

    "subjective_assessment",

    "physical_examination"
]


# =========================================================
# SAFE FALLBACKS
# =========================================================

EMPTY_RESPONSE = {

    "status": "No Match",

    "matches": [],

    "confidence_score": 0.0
}


# =========================================================
# STARTUP VALIDATION
# =========================================================

if EMBEDDING_DIM <= 0:

    raise ValueError(
        "Invalid embedding dimension"
    )

if TOP_K <= 0:

    raise ValueError(
        "TOP_K must be greater than 0"
    )

if MAX_MATCH_RESULTS <= 0:

    raise ValueError(
        "MAX_MATCH_RESULTS must be greater than 0"
    )

if MIN_SIMILARITY_SCORE < 0:

    raise ValueError(
        "MIN_SIMILARITY_SCORE invalid"
    )

if LOW_SCORE_FILTER_THRESHOLD < 0:

    raise ValueError(
        "LOW_SCORE_FILTER_THRESHOLD invalid"
    )

if REQUEST_TIMEOUT_SECONDS <= 0:

    raise ValueError(
        "REQUEST_TIMEOUT_SECONDS invalid"
    )


# =========================================================
# STARTUP LOG
# =========================================================

print("=" * 60)
print("AI Clinical Match API Configuration")
print("=" * 60)

print(f"Environment               : {ENVIRONMENT}")
print(f"Device                    : {DEVICE}")
print(f"Embedding Model           : {EMBEDDING_MODEL_NAME}")
print(f"Mongo URI                 : {MONGO_URI}")
print(f"Mongo Database            : {DATABASE_NAME}")
print(f"Mongo Collection          : {COLLECTION_NAME}")
print(f"Top K Matches             : {TOP_K}")
print(f"Max Match Results         : {MAX_MATCH_RESULTS}")
print(f"Min Similarity Score      : {MIN_SIMILARITY_SCORE}")
print(f"GPU Enabled               : {USE_GPU}")
print(f"Debug Mode                : {DEBUG_MODE}")

print("=" * 60)
print("Configuration Loaded Successfully")
print("=" * 60)