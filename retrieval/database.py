# =========================================================
# retrieval/database.py
# =========================================================

import logging
import json
import time

from typing import (
    List,
    Dict,
    Any
)

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

        # =================================================
        # CREATE CLIENT
        # =================================================

        client = MongoClient(

            MONGO_URI,

            serverSelectionTimeoutMS=
                MONGO_SERVER_SELECTION_TIMEOUT_MS,

            connectTimeoutMS=
                MONGO_CONNECT_TIMEOUT_MS,

            socketTimeoutMS=
                MONGO_SOCKET_TIMEOUT_MS
        )

        # =================================================
        # TEST CONNECTION
        # =================================================

        client.admin.command("ping")

        # =================================================
        # CONNECT DATABASE
        # =================================================

        database = client[DATABASE_NAME]

        # =================================================
        # CONNECT COLLECTION
        # =================================================

        collection = database[COLLECTION_NAME]

        # =================================================
        # GET DOCUMENT COUNT
        # =================================================

        total_documents = collection.count_documents({})

        # =================================================
        # LOG SUCCESS
        # =================================================

        log_event(

            "database_connected",

            "MongoDB connection established successfully",

            {

                "database":
                    DATABASE_NAME,

                "collection":
                    COLLECTION_NAME,

                "documents":
                    total_documents
            }
        )

        return collection

    except (
        ConnectionFailure,
        ServerSelectionTimeoutError
    ) as connection_error:

        log_event(

            "database_connection_failed",

            "MongoDB connection failed",

            {

                "error":
                    str(connection_error)
            }
        )

        client = None
        database = None
        collection = None

        return None

    except Exception as e:

        log_event(

            "database_error",

            "Unexpected MongoDB error",

            {

                "error":
                    str(e)
            }
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

                "status":
                    "Disconnected",

                "message":
                    "MongoDB client unavailable"
            }

        client.admin.command("ping")

        total_documents = 0

        if collection is not None:

            total_documents = (
                collection.count_documents({})
            )

        return {

            "status":
                "Healthy",

            "database":
                DATABASE_NAME,

            "collection":
                COLLECTION_NAME,

            "documents":
                total_documents
        }

    except Exception as e:

        return {

            "status":
                "Failed",

            "error":
                str(e)
        }


# =========================================================
# CLEAN RECORD
# =========================================================

def clean_record(
    record: Dict[str, Any],
    index: int
) -> Dict[str, Any]:

    # =====================================================
    # ENSURE RECORD IS DICTIONARY
    # =====================================================

    if not isinstance(record, dict):

        return {}

    # =====================================================
    # REMOVE MONGODB ID
    # =====================================================

    record.pop("_id", None)

    # =====================================================
    # ENSURE CASE ID
    # =====================================================

    if not record.get("case_id"):

        record["case_id"] = (
            f"CASE_{index+1}"
        )

    # =====================================================
    # BUILD SEARCHABLE TEXT
    # =====================================================

    searchable_fields = [

        str(
            record.get(
                "chief_complaint",
                ""
            )
        ),

        str(
            record.get(
                "affected_body_part",
                ""
            )
        ),

        str(
            record.get(
                "symptoms",
                ""
            )
        ),

        str(
            record.get(
                "subjective_assessment",
                ""
            )
        ),

        str(
            record.get(
                "objective_findings",
                ""
            )
        ),

        str(
            record.get(
                "doctor_notes",
                ""
            )
        ),

        str(
            record.get(
                "clinical_history",
                ""
            )
        )
    ]

    searchable_text = " ".join(
        searchable_fields
    ).strip()

    record["searchable_text"] = (
        searchable_text
    )

    # =====================================================
    # HANDLE EMBEDDINGS
    # =====================================================

    embedding = record.get(
        "embedding"
    )

    # If embedding missing
    # create empty list

    if embedding is None:

        record["embedding"] = []

    # Convert tuple to list

    elif isinstance(
        embedding,
        tuple
    ):

        record["embedding"] = list(
            embedding
        )

    # Invalid embedding format

    elif not isinstance(
        embedding,
        list
    ):

        record["embedding"] = []

    return record


# =========================================================
# FETCH CASE DATABASE
# =========================================================

def fetch_case_database() -> List[Dict[str, Any]]:

    global collection

    try:

        # =================================================
        # RECONNECT IF NEEDED
        # =================================================

        if collection is None:

            connect_database()

        if collection is None:

            log_event(

                "database_unavailable",

                "MongoDB collection unavailable"
            )

            return []

        # =================================================
        # FETCH RECORDS
        # =================================================

        records = list(
            collection.find({})
        )

        # =================================================
        # EMPTY DATABASE
        # =================================================

        if len(records) == 0:

            log_event(

                "database_empty",

                "No records found in MongoDB",

                {

                    "database":
                        DATABASE_NAME,

                    "collection":
                        COLLECTION_NAME
                }
            )

            return []

        # =================================================
        # CLEAN RECORDS
        # =================================================

        cleaned_records = []

        for index, record in enumerate(records):

            try:

                cleaned_record = clean_record(
                    record,
                    index
                )

                if cleaned_record:

                    cleaned_records.append(
                        cleaned_record
                    )

            except Exception as clean_error:

                log_event(

                    "record_clean_error",

                    "Failed to clean record",

                    {

                        "error":
                            str(clean_error)
                    }
                )

                continue

        # =================================================
        # FINAL LOG
        # =================================================

        log_event(

            "database_records_loaded",

            "Clinical cases loaded successfully",

            {

                "total_records":
                    len(cleaned_records)
            }
        )

        return cleaned_records

    except PyMongoError as mongo_error:

        log_event(

            "database_fetch_error",

            "MongoDB fetch failed",

            {

                "error":
                    str(mongo_error)
            }
        )

        return []

    except Exception as e:

        log_event(

            "database_fetch_exception",

            "Unexpected fetch error",

            {

                "error":
                    str(e)
            }
        )

        return []


# =========================================================
# INSERT CASE
# =========================================================

def insert_case(
    case_data: Dict[str, Any]
):

    global collection

    try:

        if collection is None:

            connect_database()

        if collection is None:

            return False

        if not isinstance(
            case_data,
            dict
        ):

            return False

        collection.insert_one(
            case_data
        )

        log_event(

            "case_inserted",

            "Clinical case inserted successfully",

            {

                "case_id":
                    case_data.get(
                        "case_id",
                        "Unknown"
                    )
            }
        )

        return True

    except Exception as e:

        log_event(

            "case_insert_error",

            "Failed to insert case",

            {

                "error":
                    str(e)
            }
        )

        return False


# =========================================================
# UPDATE CASE
# =========================================================

def update_case(

    case_id: str,

    update_fields: Dict[str, Any]
):

    global collection

    try:

        if collection is None:

            connect_database()

        if collection is None:

            return False

        result = collection.update_one(

            {

                "case_id":
                    case_id
            },

            {

                "$set":
                    update_fields
            }
        )

        if result.modified_count > 0:

            log_event(

                "case_updated",

                "Clinical case updated",

                {

                    "case_id":
                        case_id
                }
            )

            return True

        return False

    except Exception as e:

        log_event(

            "case_update_error",

            "Failed to update case",

            {

                "case_id":
                    case_id,

                "error":
                    str(e)
            }
        )

        return False


# =========================================================
# DELETE CASE
# =========================================================

def delete_case(
    case_id: str
):

    global collection

    try:

        if collection is None:

            connect_database()

        if collection is None:

            return False

        result = collection.delete_one(

            {

                "case_id":
                    case_id
            }
        )

        if result.deleted_count > 0:

            log_event(

                "case_deleted",

                "Clinical case deleted",

                {

                    "case_id":
                        case_id
                }
            )

            return True

        return False

    except Exception as e:

        log_event(

            "case_delete_error",

            "Failed to delete case",

            {

                "case_id":
                    case_id,

                "error":
                    str(e)
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

            {

                "error":
                    str(e)
            }
        )


# =========================================================
# MAIN TEST
# =========================================================

if __name__ == "__main__":

    print("\n===================================")
    print("DATABASE CONNECTION TEST")
    print("===================================\n")

    health = database_health_check()

    print(

        json.dumps(
            health,
            indent=4
        )
    )

    cases = fetch_case_database()

    print(
        f"\nLoaded Cases: {len(cases)}"
    )

    if len(cases) > 0:

        print("\nSample Case:\n")

        print(

            json.dumps(
                cases[0],
                indent=4
            )[:1000]
        )

    print("\n===================================\n")