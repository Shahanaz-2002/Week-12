# =========================================================
# IMPORTS
# =========================================================

import logging

import json

import time

import numpy as np

from datetime import datetime

from typing import List, Dict, Any


from retrieval.database import collection

from retrieval.embedding import BioBERTEmbedding

from config import EMBEDDING_VERSION


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
# EMBEDDER INITIALIZATION
# =========================================================

try:

    embedder = BioBERTEmbedding()

    logger.info(

        json.dumps({

            "event":
                "embedder_initialized",

            "message":
                "BioBERTEmbedding initialized successfully",

            "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S")
        })
    )

except Exception as e:

    embedder = None

    logger.error(

        json.dumps({

            "event":
                "embedder_initialization_failed",

            "error":
                str(e),

            "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S")
        })
    )


# =========================================================
# LOGGING HELPER
# =========================================================

def log_event(

    event_type,

    message,

    extra=None
):

    log_data = {

        "event":
            event_type,

        "message":
            message,

        "timestamp":
            time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if extra:

        log_data.update(extra)

    logger.info(
        json.dumps(log_data)
    )


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):

    if text is None:

        return ""

    text = str(text)

    text = text.strip()

    text = " ".join(
        text.split()
    )

    return text


# =========================================================
# SAFE FIELD EXTRACTION
# =========================================================

def safe_field(

    record,

    field_name,

    default=""
):

    try:

        value = record.get(
            field_name,
            default
        )

        if value in [None, "", [], {}]:

            return default

        return clean_text(value)

    except Exception:

        return default


# =========================================================
# BUILD CLINICAL TEXT
# =========================================================

def build_clinical_text(

    record: Dict[str, Any]

) -> str:

    text_parts = [

        safe_field(
            record,
            "chief_complaint"
        ),

        safe_field(
            record,
            "affected_body_part"
        ),

        safe_field(
            record,
            "symptoms"
        ),

        safe_field(
            record,
            "diagnosis"
        ),

        safe_field(
            record,
            "subjective_assessment"
        ),

        safe_field(
            record,
            "functional_assessment"
        ),

        safe_field(
            record,
            "physical_examination"
        ),

        safe_field(
            record,
            "objective_findings"
        ),

        safe_field(
            record,
            "patient_pain_classification"
        ),

        safe_field(
            record,
            "clinical_history"
        ),

        safe_field(
            record,
            "doctor_notes"
        ),

        safe_field(
            record,
            "previous_injuries"
        ),

        safe_field(
            record,
            "current_medications"
        ),

        safe_field(
            record,
            "allergies"
        ),

        safe_field(
            record,
            "symptoms_duration"
        ),

        safe_field(
            record,
            "resolution_notes"
        ),

        safe_field(
            record,
            "case_description"
        )
    ]

    filtered_parts = [

        part

        for part in text_parts

        if part not in [None, ""]
    ]

    return " | ".join(
        filtered_parts
    )


# =========================================================
# VALIDATE EMBEDDING
# =========================================================

def validate_embedding(
    embedding
):

    try:

        if embedding is None:

            return False

        embedding = np.array(
            embedding
        )

        if embedding.size == 0:

            return False

        if len(embedding.shape) != 1:

            return False

        return True

    except Exception:

        return False


# =========================================================
# GENERATE AND STORE EMBEDDINGS
# =========================================================

def generate_and_store_embeddings():

    # =====================================================
    # EMBEDDER CHECK
    # =====================================================

    if embedder is None:

        log_event(
            "embedder_error",
            "Embedding model unavailable"
        )

        return

    # =====================================================
    # DATABASE CHECK
    # =====================================================

    if collection is None:

        log_event(
            "database_unavailable",
            "MongoDB collection unavailable"
        )

        return

    # =====================================================
    # FETCH RECORDS
    # =====================================================

    try:

        records = list(
            collection.find({})
        )

        total_records = len(
            records
        )

    except Exception as e:

        log_event(
            "database_error",
            "Failed to fetch records",
            {
                "error":
                    str(e)
            }
        )

        return

    # =====================================================
    # COUNTERS
    # =====================================================

    processed = 0

    skipped = 0

    errors = 0

    updated = 0

    start_time = time.time()

    # =====================================================
    # START LOG
    # =====================================================

    log_event(

        "embedding_generation_started",

        "Clinical embedding generation started",

        {
            "total_records":
                total_records,

            "embedding_version":
                EMBEDDING_VERSION
        }
    )

    # =====================================================
    # PROCESS RECORDS
    # =====================================================

    for record in records:

        try:

            case_id = str(

                record.get(
                    "case_id",
                    "Unknown"
                )
            )

            # ------------------------------------------------
            # SKIP EXISTING EMBEDDINGS
            # ------------------------------------------------

            existing_embedding = record.get(
                "embedding",
                None
            )

            existing_version = record.get(
                "embedding_version",
                ""
            )

            if (

                validate_embedding(
                    existing_embedding
                )

                and

                existing_version == EMBEDDING_VERSION
            ):

                skipped += 1

                continue

            # ------------------------------------------------
            # BUILD SEARCHABLE TEXT
            # ------------------------------------------------

            text = build_clinical_text(
                record
            )

            if not text:

                skipped += 1

                log_event(
                    "empty_text_skipped",
                    "Empty clinical text skipped",
                    {
                        "case_id":
                            case_id
                    }
                )

                continue

            # ------------------------------------------------
            # GENERATE EMBEDDING
            # ------------------------------------------------

            embedding_start = time.time()

            # =============================================
            # FIXED METHOD NAME
            # =============================================

            embedding = embedder.generate_embedding(
                text
            )

            embedding_time = round(

                (
                    time.time() -
                    embedding_start
                ) * 1000,

                2
            )

            if not validate_embedding(
                embedding
            ):

                errors += 1

                log_event(
                    "embedding_failed",
                    "Embedding generation failed",
                    {
                        "case_id":
                            case_id
                    }
                )

                continue

            # ------------------------------------------------
            # CONVERT TO LIST
            # ------------------------------------------------

            embedding = np.array(
                embedding,
                dtype=np.float32
            ).tolist()

            # ------------------------------------------------
            # STORE IN DATABASE
            # ------------------------------------------------

            update_result = collection.update_one(

                {
                    "case_id":
                        case_id
                },

                {
                    "$set": {

                        "embedding":
                            embedding,

                        "embedding_text":
                            text,

                        "embedding_dimension":
                            len(embedding),

                        "embedding_version":
                            EMBEDDING_VERSION,

                        "embedding_created_at":
                            datetime.utcnow(),

                        "embedding_model":
                            "BioBERT",

                        "embedding_domain":
                            "Clinical",

                        "embedding_updated":
                            True
                    }
                }
            )

            processed += 1

            if update_result.modified_count > 0:

                updated += 1

            # ------------------------------------------------
            # SUCCESS LOG
            # ------------------------------------------------

            log_event(

                "embedding_stored",

                "Clinical embedding stored successfully",

                {
                    "case_id":
                        case_id,

                    "embedding_dimension":
                        len(embedding),

                    "embedding_time_ms":
                        embedding_time,

                    "processed":
                        processed
                }
            )

        # =================================================
        # RECORD ERROR
        # =================================================

        except Exception as e:

            errors += 1

            log_event(

                "record_processing_error",

                "Error processing clinical case",

                {
                    "case_id":
                        record.get(
                            "case_id",
                            "Unknown"
                        ),

                    "error":
                        str(e)
                }
            )

            continue

    # =====================================================
    # FINAL SUMMARY
    # =====================================================

    total_time = round(

        (
            time.time() -
            start_time
        ) * 1000,

        2
    )

    summary = {

        "processed":
            processed,

        "updated":
            updated,

        "skipped":
            skipped,

        "errors":
            errors,

        "total_records":
            total_records,

        "total_time_ms":
            total_time,

        "embedding_version":
            EMBEDDING_VERSION
    }

    log_event(

        "embedding_generation_completed",

        "Clinical embedding generation completed",

        summary
    )

    # =====================================================
    # TERMINAL SUMMARY
    # =====================================================

    print("\n=================================================")

    print(
        "CLINICAL EMBEDDING GENERATION COMPLETED"
    )

    print("=================================================")

    print(
        f"Total Records       : {total_records}"
    )

    print(
        f"Processed           : {processed}"
    )

    print(
        f"Updated             : {updated}"
    )

    print(
        f"Skipped             : {skipped}"
    )

    print(
        f"Errors              : {errors}"
    )

    print(
        f"Embedding Version   : {EMBEDDING_VERSION}"
    )

    print(
        f"Time Taken (ms)     : {total_time}"
    )

    print("=================================================\n")


# =========================================================
# MAIN ENTRY
# =========================================================

if __name__ == "__main__":

    generate_and_store_embeddings()