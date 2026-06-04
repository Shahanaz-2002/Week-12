# =========================================================
# api/main.py
# =========================================================

# =========================================================
# IMPORTS
# =========================================================

import time
import logging
import uuid
import json
import traceback

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status
)

from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from fastapi.exceptions import RequestValidationError

import uvicorn

from models.models import (
    ClinicalMatchRequest,
    ClinicalMatchResponse
)

from services.analyze_service import (
    clinical_match_pipeline
)

# =========================================================
# API CONFIGURATION
# =========================================================

API_VERSION = "6.0.0"

APP_NAME = "Clinical Match API"

MAX_MATCHES = 2

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
# STANDARD RESPONSE HELPERS
# =========================================================

def generate_request_id() -> str:

    return str(uuid.uuid4())


def current_timestamp() -> str:

    return time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def standard_error_response(

    status_text: str,

    message: str,

    request_id: str,

    error: Any = None

) -> Dict[str, Any]:

    return {

        "status":
            status_text,

        "message":
            message,

        "request_id":
            request_id,

        "api_version":
            API_VERSION,

        "timestamp":
            current_timestamp(),

        "error":
            error
    }

# =========================================================
# LOG EVENT FUNCTION
# =========================================================

def log_event(

    event_type: str,

    request_id: str,

    message: str,

    extra: Dict[str, Any] = None
):

    log_data = {

        "event":
            event_type,

        "request_id":
            request_id,

        "message":
            message,

        "timestamp":
            current_timestamp()
    }

    if extra:

        log_data.update(extra)

    logger.info(
        json.dumps(
            log_data,
            default=str
        )
    )

# =========================================================
# APPLICATION LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(

        json.dumps({

            "event":
                "startup",

            "message":
                f"{APP_NAME} Started",

            "version":
                API_VERSION,

            "timestamp":
                current_timestamp()
        })
    )

    yield

    logger.info(

        json.dumps({

            "event":
                "shutdown",

            "message":
                f"{APP_NAME} Shutdown",

            "version":
                API_VERSION,

            "timestamp":
                current_timestamp()
        })
    )

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(

    title=APP_NAME,

    version=API_VERSION,

    description="""
AI-Powered Clinical Similarity Matching API

Features:
- Dynamic Optional Clinical Input Processing
- Semantic Similarity Retrieval
- Top Clinical Patient Matching
- Clinical Recommendation Generation
- Confidence Score Analysis
- Error Stabilization & Validation
- Swagger/OpenAPI Documentation
- Structured Error Handling
- API Health Monitoring
""",

    lifespan=lifespan
)

# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)

# =========================================================
# VALIDATION HANDLER
# =========================================================

@app.exception_handler(
    RequestValidationError
)

async def validation_exception_handler(

    request: Request,

    exc: RequestValidationError
):

    request_id = generate_request_id()

    log_event(

        "validation_error",

        request_id,

        "Request validation failed",

        {
            "errors":
                exc.errors()
        }
    )

    return JSONResponse(

        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,

        content=standard_error_response(

            status_text="Failed",

            message="Validation Error",

            request_id=request_id,

            error=exc.errors()
        )
    )

# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================

@app.exception_handler(Exception)

async def global_exception_handler(

    request: Request,

    exc: Exception
):

    request_id = generate_request_id()

    log_event(

        "global_exception",

        request_id,

        "Unhandled exception occurred",

        {
            "error":
                str(exc),

            "traceback":
                traceback.format_exc()
        }
    )

    return JSONResponse(

        status_code=500,

        content=standard_error_response(

            status_text="Failed",

            message="Internal Server Error",

            request_id=request_id,

            error=str(exc)
        )
    )

# =========================================================
# ROOT ROUTE
# =========================================================

@app.get("/")

def root():

    return {

        "message":
            f"{APP_NAME} Running",

        "version":
            API_VERSION,

        "status":
            "active",

        "docs":
            "/docs",

        "redoc":
            "/redoc"
    }

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")

def health_check():

    return {

        "status":
            "healthy",

        "api":
            APP_NAME,

        "version":
            API_VERSION,

        "timestamp":
            current_timestamp(),

        "server":
            "FastAPI + Uvicorn"
    }

# =========================================================
# DEBUG ROUTE
# =========================================================

@app.get("/debug/sample")

def debug_sample():

    return {

        "sample_query":
            "Knee pain | ACL injury | swelling",

        "sample_context":
            "Patient with chronic knee pain and swelling",

        "sample_fields": [

            "chief_complaint",

            "affected_body_part",

            "symptoms_duration",

            "subjective_assessment",

            "physical_examination"
        ]
    }

# =========================================================
# MAIN CLINICAL MATCH ENDPOINT
# =========================================================

@app.post(

    "/clinical/match",

    response_model=ClinicalMatchResponse
)

def clinical_match(

    request: ClinicalMatchRequest
):

    request_id = generate_request_id()

    start_time = time.time()

    log_event(

        "request_received",

        request_id,

        "Clinical request received"
    )

    try:

        # =================================================
        # GENERATE DYNAMIC INPUTS
        # =================================================

        processed_inputs = (
            request.generate_dynamic_inputs()
        )

        if not isinstance(
            processed_inputs,
            dict
        ):

            processed_inputs = {}

        search_query = processed_inputs.get(
            "search_query",
            ""
        )

        generated_context = processed_inputs.get(
            "generated_context",
            ""
        )

        combined_symptoms = processed_inputs.get(
            "combined_symptoms",
            ""
        )

        patient_metadata = processed_inputs.get(
            "patient_metadata",
            {}
        )

        available_fields = processed_inputs.get(
            "available_fields",
            []
        )

        # =================================================
        # VALIDATE SEARCH QUERY
        # =================================================

        if not str(search_query).strip():

            raise HTTPException(

                status_code=400,

                detail={

                    "status":
                        "Failed",

                    "message":
                        "No valid clinical input fields provided"
                }
            )

        # =================================================
        # EXECUTE PIPELINE
        # =================================================

        result = clinical_match_pipeline(

            request=request,

            request_id=request_id,

            search_query=search_query,

            generated_context=generated_context,

            combined_symptoms=combined_symptoms,

            patient_metadata=patient_metadata,

            log_event=log_event
        )

        if not isinstance(
            result,
            dict
        ):

            result = {}

        # =================================================
        # SAFE EXTRACTION
        # =================================================

        matches = result.get(
            "matches",
            []
        )

        if not isinstance(
            matches,
            list
        ):

            matches = []

        matches = matches[:MAX_MATCHES]

        try:

            confidence_score = float(
                result.get(
                    "confidence_score",
                    0.0
                )
            )

        except Exception:

            confidence_score = 0.0

        confidence_score = round(
            max(
                0.0,
                min(1.0, confidence_score)
            ),
            4
        )

        processing_time = round(

            (
                time.time() -
                start_time
            ) * 1000,

            2
        )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        final_response = {

            "status":
                result.get(
                    "status",
                    "Success"
                ),

            "message":
                result.get(
                    "message",
                    "Clinical matching completed successfully"
                ),

            "request_id":
                request_id,

            "api_version":
                API_VERSION,

            "request_timestamp":
                current_timestamp(),

            "matches":
                matches,

            "total_matches_found":
                len(matches),

            "confidence_score":
                confidence_score,

            "search_query":
                search_query,

            "generated_context":
                generated_context,

            "combined_symptoms":
                combined_symptoms,

            "input_fields_used":
                available_fields,

            "processing_time_ms":
                processing_time,

            "patient_metadata":
                patient_metadata,

            "explanation":
                result.get(
                    "explanation",
                    "Semantic clinical retrieval completed"
                ),

            "warnings":
                [],

            "success":
                True
        }

        log_event(

            "response_generated",

            request_id,

            "Clinical response generated",

            {
                "matches_found":
                    len(matches),

                "processing_time_ms":
                    processing_time,

                "confidence_score":
                    confidence_score
            }
        )

        return ClinicalMatchResponse(
            **final_response
        )

    # =====================================================
    # HTTP EXCEPTIONS
    # =====================================================

    except HTTPException as http_error:

        log_event(

            "http_error",

            request_id,

            "HTTP exception occurred",

            {
                "status_code":
                    http_error.status_code,

                "detail":
                    str(http_error.detail)
            }
        )

        raise http_error

    # =====================================================
    # UNEXPECTED ERRORS
    # =====================================================

    except Exception as e:

        log_event(

            "pipeline_failure",

            request_id,

            "Clinical pipeline failure",

            {
                "error":
                    str(e),

                "traceback":
                    traceback.format_exc()
            }
        )

        raise HTTPException(

            status_code=500,

            detail=standard_error_response(

                status_text="Failed",

                message="Internal clinical pipeline failure",

                request_id=request_id,

                error=str(e)
            )
        )

# =========================================================
# SERVER START
# =========================================================

if __name__ == "__main__":

    uvicorn.run(

        "api.main:app",

        host="0.0.0.0",

        port=8000,

        reload=True,

        log_level="info"
    )