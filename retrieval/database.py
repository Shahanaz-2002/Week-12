# =========================================================
# retrieval/database.py
# =========================================================

import logging
import json
import time
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    PyMongoError
)

from config import (
    MONGO_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
    MONGO_SERVER_SELECTION_TIMEOUT_MS,
    MONGO_CONNECT_TIMEOUT_MS,
    MONGO_SOCKET_TIMEOUT_MS
)

# =========================================================
# LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    force=True
)

logger = logging.getLogger(__name__)

# =========================================================
# LOG EVENT
# =========================================================

def log_event(event_type, message, extra=None):
    log_data = {
        "event": event_type,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if extra:
        log_data.update(extra)
        
    logger.info(json.dumps(log_data))

# =========================================================
# GLOBAL DATABASE VARIABLES
# =========================================================

client = None
database = None
collection = None

# =========================================================
# CONNECT DATABASE
# =========================================================

def connect_database():
    global client
    global database
    global collection

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
            socketTimeoutMS=MONGO_SOCKET_TIMEOUT_MS
        )

        client.admin.command("ping")

        database = client[DATABASE_NAME]
        collection = database[COLLECTION_NAME]

        total_documents = collection.count_documents({})

        log_event(
            "database_connected",
            "MongoDB connection established successfully",
            {
                "database": DATABASE_NAME,
                "collection": COLLECTION_NAME,
                "documents": total_documents
            }
        )

        return collection

    except (ConnectionFailure, ServerSelectionTimeoutError) as connection_error:
        log_event(
            "database_connection_failed",
            "MongoDB connection failed",
            {"error": str(connection_error)}
        )
        client = None
        database = None
        collection = None
        return None

    except Exception as e:
        log_event(
            "database_error",
            "Unexpected MongoDB error",
            {"error": str(e)}
        )
        client = None
        database = None
        collection = None
        return None

# =========================================================
# INITIALIZE DATABASE CONNECTION
# =========================================================

connect_database()

# =========================================================
# DATABASE HEALTH CHECK
# =========================================================

def database_health_check():
    global client
    global collection

    try:
        if client is None:
            return {
                "status": "Disconnected",
                "message": "MongoDB client unavailable"
            }

        client.admin.command("ping")
        total_documents = 0

        if collection is not None:
            total_documents = collection.count_documents({})

        return {
            "status": "Healthy",
            "database": DATABASE_NAME,
            "collection": COLLECTION_NAME,
            "documents": total_documents
        }

    except Exception as e:
        return {
            "status": "Failed",
            "error": str(e)
        }

# =========================================================
# CLEAN RECORD
# =========================================================

def clean_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    if not isinstance(record, dict):
        return {}

    record.pop("_id", None)

    if not record.get("case_id"):
        record["case_id"] = f"CASE_{index+1}"

    record.setdefault("diagnosis", "")
    record.setdefault("assessment_notes", "")
    record.setdefault("symptoms", "")
    record.setdefault("doctor_notes", "")
    record.setdefault("clinical_history", "")

    text_fields = [
        "diagnosis",
        "assessment_notes",
        "symptoms",
        "doctor_notes",
        "clinical_history",
        "skin_condition",
        "affected_skin_area",
        "chief_complaint",
        "objective_findings",
        "subjective_assessment"
    ]

    for field in text_fields:
        value = record.get(field)
        if value is None:
            record[field] = ""
        else:
            record[field] = str(value).strip()

    searchable_fields = [
        record["diagnosis"],
        record["assessment_notes"],
        record["symptoms"],
        record["doctor_notes"],
        record["clinical_history"],
        record.get("skin_condition", ""),
        record.get("affected_skin_area", ""),
        record.get("chief_complaint", ""),
        record.get("objective_findings", ""),
        record.get("subjective_assessment", "")
    ]

    searchable_text = " ".join(
        [str(field) for field in searchable_fields if field]
    ).strip()

    record["searchable_text"] = searchable_text

    embedding = record.get("embedding")

    if embedding is None:
        record["embedding"] = []
    elif isinstance(embedding, tuple):
        record["embedding"] = list(embedding)
    elif not isinstance(embedding, list):
        record["embedding"] = []
    else:
        try:
            record["embedding"] = [float(x) for x in embedding]
        except Exception:
            record["embedding"] = []

    if not record.get("diagnosis"):
        record["diagnosis"] = ""
    if not record.get("assessment_notes"):
        record["assessment_notes"] = ""
    if not record.get("symptoms"):
        record["symptoms"] = ""
    if not record.get("doctor_notes"):
        record["doctor_notes"] = ""

    return record

# =========================================================
# FETCH CASE DATABASE
# =========================================================

def fetch_case_database() -> List[Dict[str, Any]]:
    global collection

    try:
        if collection is None:
            connect_database()

        if collection is None:
            log_event(
                "database_unavailable",
                "MongoDB collection unavailable"
            )
            return []

        records = list(collection.find({}))

        if len(records) == 0:
            log_event(
                "database_empty",
                "No records found in MongoDB",
                {
                    "database": DATABASE_NAME,
                    "collection": COLLECTION_NAME
                }
            )
            return []

        cleaned_records = [clean_record(rec, idx) for idx, rec in enumerate(records)]

        log_event(
            "database_records_loaded",
            "Clinical cases loaded successfully",
            {"total_records": len(cleaned_records)}
        )

        return cleaned_records

    except PyMongoError as mongo_error:
        log_event(
            "database_fetch_error",
            "MongoDB fetch failed",
            {"error": str(mongo_error)}
        )
        return []

    except Exception as e:
        log_event(
            "database_fetch_exception",
            "Unexpected fetch error",
            {"error": str(e)}
        )
        return []

# =========================================================
# INSERT CASE
# =========================================================

def insert_case(case_data: Dict[str, Any]):
    global collection

    try:
        if collection is None:
            connect_database()

        if collection is None:
            return False

        if not isinstance(case_data, dict):
            return False

        collection.insert_one(case_data)

        log_event(
            "case_inserted",
            "Clinical case inserted successfully",
            {"case_id": case_data.get("case_id", "Unknown")}
        )

        return True

    except Exception as e:
        log_event(
            "case_insert_error",
            "Failed to insert case",
            {"error": str(e)}
        )
        return False

# =========================================================
# UPDATE CASE
# =========================================================

def update_case(case_id: str, update_fields: Dict[str, Any]):
    global collection

    try:
        if collection is None:
            connect_database()

        if collection is None:
            return False

        result = collection.update_one(
            {"case_id": case_id},
            {"$set": update_fields}
        )

        if result.modified_count > 0:
            log_event(
                "case_updated",
                "Clinical case updated",
                {"case_id": case_id}
            )
            return True

        return False

    except Exception as e:
        log_event(
            "case_update_error",
            "Failed to update case",
            {
                "case_id": case_id,
                "error": str(e)
            }
        )
        return False

# =========================================================
# DELETE CASE
# =========================================================

def delete_case(case_id: str):
    global collection

    try:
        if collection is None:
            connect_database()

        if collection is None:
            return False

        result = collection.delete_one({"case_id": case_id})

        if result.deleted_count > 0:
            log_event(
                "case_deleted",
                "Clinical case deleted",
                {"case_id": case_id}
            )
            return True

        return False

    except Exception as e:
        log_event(
            "case_delete_error",
            "Failed to delete case",
            {
                "case_id": case_id,
                "error": str(e)
            }
        )
        return False

# =========================================================
# CLOSE DATABASE CONNECTION
# =========================================================

def close_database_connection():
    global client

    try:
        if client is not None:
            client.close()
            log_event(
                "database_connection_closed",
                "MongoDB connection closed"
            )
    except Exception as e:
        log_event(
            "database_close_error",
            "Failed to close MongoDB connection",
            {"error": str(e)}
        )        