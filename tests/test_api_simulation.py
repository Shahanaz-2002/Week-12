import requests
import json
import time
import uuid
from typing import Dict, Any, List


# =========================================================
# API CONFIGURATION
# =========================================================

API_URL = "http://127.0.0.1:8000/clinical/match"

REQUEST_TIMEOUT = 30

MAX_ALLOWED_RESPONSE_MS = 5000


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def print_divider():

    print("=" * 120)


def generate_request_id():

    return f"REQ-{uuid.uuid4().hex[:8].upper()}"


def safe_float(value, default=0.0):

    try:

        return float(value)

    except Exception:

        return default


def safe_list(value):

    if isinstance(value, list):

        return value

    return []


# =========================================================
# SUCCESS RESPONSE VALIDATION
# =========================================================

def validate_success_response(data):

    required_fields = [

        "status",
        "message",
        "matches",
        "total_matches_found",
        "confidence_score",
        "generated_context",
        "search_query",
        "processing_time_ms",
        "explanation",
        "request_id",
        "api_version"
    ]

    # =====================================================
    # REQUIRED FIELD VALIDATION
    # =====================================================

    for field in required_fields:

        if field not in data:

            return (
                False,
                f"Missing field: {field}"
            )

    # =====================================================
    # STATUS VALIDATION
    # =====================================================

    allowed_status = [

        "Success",
        "No Match"
    ]

    if data["status"] not in allowed_status:

        return (
            False,
            "Invalid status value"
        )

    # =====================================================
    # TYPE VALIDATION
    # =====================================================

    if not isinstance(data["matches"], list):

        return (
            False,
            "matches should be a list"
        )

    if not isinstance(
        data["confidence_score"],
        (float, int)
    ):

        return (
            False,
            "confidence_score must be numeric"
        )

    # =====================================================
    # CONFIDENCE SCORE VALIDATION
    # =====================================================

    confidence_score = safe_float(
        data["confidence_score"]
    )

    if not (
        0.0 <= confidence_score <= 1.0
    ):

        return (
            False,
            "confidence_score out of range"
        )

    # =====================================================
    # MATCH COUNT VALIDATION
    # =====================================================

    if data["total_matches_found"] != len(data["matches"]):

        return (
            False,
            "total_matches_found mismatch"
        )

    # =====================================================
    # TOP 2 VALIDATION
    # =====================================================

    if len(data["matches"]) > 2:

        return (
            False,
            "More than 2 matches returned"
        )

    # =====================================================
    # MATCH VALIDATION
    # =====================================================

    allowed_confidence_levels = [

        "High",
        "Moderate",
        "Low"
    ]

    for match in data["matches"]:

        required_match_fields = [

            "case_id",
            "match_score",
            "confidence_level",
            "chief_complaint",
            "affected_body_part",
            "doctor_notes",
            "matched_keywords",
            "semantic_score",
            "retrieval_source",
            "recommendation",
            "explanation"
        ]

        for field in required_match_fields:

            if field not in match:

                return (
                    False,
                    f"Missing match field: {field}"
                )

        # -------------------------------------------------
        # SCORE VALIDATION
        # -------------------------------------------------

        match_score = safe_float(
            match["match_score"]
        )

        if not (
            0.0 <= match_score <= 1.0
        ):

            return (
                False,
                "match_score out of range"
            )

        # -------------------------------------------------
        # CONFIDENCE LEVEL VALIDATION
        # -------------------------------------------------

        if (
            match["confidence_level"]
            not in allowed_confidence_levels
        ):

            return (
                False,
                "Invalid confidence level"
            )

        # -------------------------------------------------
        # RECOMMENDATION VALIDATION
        # -------------------------------------------------

        recommendation = match.get(
            "recommendation",
            {}
        )

        if not isinstance(
            recommendation,
            dict
        ):

            return (
                False,
                "recommendation must be dict"
            )

        if "recommended_tests" not in recommendation:

            return (
                False,
                "Missing recommended_tests"
            )

        if "recommended_medicines" not in recommendation:

            return (
                False,
                "Missing recommended_medicines"
            )

        if not isinstance(
            recommendation["recommended_tests"],
            list
        ):

            return (
                False,
                "recommended_tests must be list"
            )

        if not isinstance(
            recommendation["recommended_medicines"],
            list
        ):

            return (
                False,
                "recommended_medicines must be list"
            )

        # -------------------------------------------------
        # MATCHED KEYWORDS VALIDATION
        # -------------------------------------------------

        if not isinstance(
            match["matched_keywords"],
            list
        ):

            return (
                False,
                "matched_keywords must be list"
            )

    return (
        True,
        "Valid success response"
    )


# =========================================================
# ERROR RESPONSE VALIDATION
# =========================================================

def validate_error_response(data):

    if not isinstance(data, dict):

        return (
            False,
            "Error response should be dict"
        )

    if "detail" not in data:

        return (
            False,
            "Missing detail field"
        )

    return (
        True,
        "Valid error response"
    )


# =========================================================
# PRINT RESULT
# =========================================================

def print_test_result(
    passed,
    message
):

    if passed:

        print(f"\nPASS : {message}")

    else:

        print(f"\nFAIL : {message}")


# =========================================================
# PRINT MATCHES
# =========================================================

def print_match_summary(matches):

    if not matches:

        print("\nNo matches found")

        return

    print("\nTOP MATCHES SUMMARY:\n")

    for index, match in enumerate(matches, start=1):

        print(f"Match #{index}")

        print(
            f"Case ID           : "
            f"{match.get('case_id')}"
        )

        print(
            f"Match Score       : "
            f"{match.get('match_score')}"
        )

        print(
            f"Confidence Level  : "
            f"{match.get('confidence_level')}"
        )

        print(
            f"Chief Complaint   : "
            f"{match.get('chief_complaint')}"
        )

        print(
            f"Affected Body Part: "
            f"{match.get('affected_body_part')}"
        )

        recommendation = match.get(
            "recommendation",
            {}
        )

        print(
            f"Recommended Tests : "
            f"{recommendation.get('recommended_tests', [])}"
        )

        print(
            f"Recommended Medicines : "
            f"{recommendation.get('recommended_medicines', [])}"
        )

        print("-" * 80)


# =========================================================
# SEND REQUEST
# =========================================================

def send_request(
    payload: Dict[str, Any],
    test_name: str,
    expected_status: int
):

    print_divider()

    print(f"TEST NAME  : {test_name}")

    request_id = generate_request_id()

    print(f"REQUEST ID : {request_id}")

    print("\nREQUEST PAYLOAD:\n")

    print(
        json.dumps(
            payload,
            indent=4
        )
    )

    start_time = time.time()

    try:

        # =================================================
        # API REQUEST
        # =================================================

        response = requests.post(

            API_URL,

            json=payload,

            timeout=REQUEST_TIMEOUT
        )

        response_time = round(

            (
                time.time() -
                start_time
            ) * 1000,

            2
        )

        print(f"\nSTATUS CODE   : {response.status_code}")

        print(f"RESPONSE TIME : {response_time} ms")

        # =================================================
        # PERFORMANCE WARNING
        # =================================================

        if response_time > MAX_ALLOWED_RESPONSE_MS:

            print(
                "\nWARNING : Slow API response"
            )

        # =================================================
        # JSON PARSING
        # =================================================

        try:

            data = response.json()

            print("\nRESPONSE JSON:\n")

            print(
                json.dumps(
                    data,
                    indent=4
                )
            )

        except Exception:

            print_test_result(
                False,
                "Invalid JSON response"
            )

            return False

        # =================================================
        # STATUS VALIDATION
        # =================================================

        if response.status_code != expected_status:

            print_test_result(

                False,

                (
                    f"Expected {expected_status}, "
                    f"got {response.status_code}"
                )
            )

            return False

        # =================================================
        # RESPONSE VALIDATION
        # =================================================

        if response.status_code == 200:

            is_valid, validation_message = (

                validate_success_response(
                    data
                )
            )

        else:

            is_valid, validation_message = (

                validate_error_response(
                    data
                )
            )

        if not is_valid:

            print_test_result(
                False,
                validation_message
            )

            return False

        print_test_result(
            True,
            validation_message
        )

        # =================================================
        # MATCH SUMMARY
        # =================================================

        if response.status_code == 200:

            print_match_summary(
                data.get(
                    "matches",
                    []
                )
            )

        return True

    # =====================================================
    # CONNECTION ERROR
    # =====================================================

    except requests.exceptions.ConnectionError:

        print_test_result(
            False,
            "Unable to connect to API"
        )

        return False

    # =====================================================
    # TIMEOUT ERROR
    # =====================================================

    except requests.exceptions.Timeout:

        print_test_result(
            False,
            "Request timeout"
        )

        return False

    # =====================================================
    # UNKNOWN ERROR
    # =====================================================

    except Exception as e:

        print_test_result(
            False,
            f"Unexpected error -> {e}"
        )

        return False


# =========================================================
# TEST CASES
# =========================================================

test_cases = [

    # =====================================================
    # FULL CLINICAL INPUT
    # =====================================================

    {
        "name": "Full Clinical Input",

        "payload": {

            "chief_complaint":
                "Right knee pain while climbing stairs",

            "affected_body_part":
                "Right Knee",

            "symptoms_duration":
                "3 weeks",

            "previous_injuries":
                "ACL tear 2 years ago",

            "current_medications":
                "Ibuprofen",

            "allergies":
                "Penicillin",

            "occupation":
                "Construction Worker",

            "activity_levels":
                "High",

            "gender":
                "Male",

            "age":
                35,

            "doctor_name":
                "Dr Kumar",

            "subjective_assessment":
                "Pain increases during movement",

            "functional_assessment":
                "Difficulty squatting",

            "physical_examination":
                "Swelling near patella",

            "objective_findings":
                "Reduced range of motion",

            "patient_pain_classification":
                "Moderate",

            "doctor_notes":
                "Possible ligament instability"
        },

        "expected_status":
            200
    },

    # =====================================================
    # PARTIAL INPUT
    # =====================================================

    {
        "name": "Partial Clinical Input",

        "payload": {

            "chief_complaint":
                "Lower back pain",

            "occupation":
                "Driver",

            "age":
                45
        },

        "expected_status":
            200
    },

    # =====================================================
    # SHOULDER CASE
    # =====================================================

    {
        "name": "Shoulder Clinical Input",

        "payload": {

            "chief_complaint":
                "Shoulder stiffness and pain",

            "affected_body_part":
                "Left Shoulder",

            "physical_examination":
                "Limited range of motion",

            "patient_pain_classification":
                "Severe"
        },

        "expected_status":
            200
    },

    # =====================================================
    # EMPTY REQUEST
    # =====================================================

    {
        "name": "Empty Request",

        "payload": {},

        "expected_status":
            422
    },

    # =====================================================
    # INVALID AGE
    # =====================================================

    {
        "name": "Invalid Age",

        "payload": {

            "chief_complaint":
                "Neck pain",

            "age":
                150
        },

        "expected_status":
            422
    },

    # =====================================================
    # INVALID GENDER
    # =====================================================

    {
        "name": "Invalid Gender",

        "payload": {

            "chief_complaint":
                "Back pain",

            "gender":
                "Alien"
        },

        "expected_status":
            422
    },

    # =====================================================
    # NO MATCH CASE
    # =====================================================

    {
        "name": "No Match Scenario",

        "payload": {

            "chief_complaint":
                "Rare unknown neurological issue",

            "affected_body_part":
                "Brain"
        },

        "expected_status":
            200
    }
]


# =========================================================
# MAIN EXECUTION
# =========================================================

if __name__ == "__main__":

    print(
        "\nStarting Clinical Match "
        "API Simulation...\n"
    )

    passed = 0

    failed = 0

    results_summary: List[Dict] = []

    total_start_time = time.time()

    # =====================================================
    # EXECUTE TESTS
    # =====================================================

    for test in test_cases:

        result = send_request(

            payload=test["payload"],

            test_name=test["name"],

            expected_status=test["expected_status"]
        )

        if result:

            passed += 1

            results_summary.append({

                "test":
                    test["name"],

                "status":
                    "PASS"
            })

        else:

            failed += 1

            results_summary.append({

                "test":
                    test["name"],

                "status":
                    "FAIL"
            })

    # =====================================================
    # FINAL SUMMARY
    # =====================================================

    total_execution_time = round(

        (
            time.time() -
            total_start_time
        ) * 1000,

        2
    )

    print_divider()

    print("FINAL SUMMARY\n")

    print(f"TOTAL TESTS        : {len(test_cases)}")

    print(f"PASSED             : {passed}")

    print(f"FAILED             : {failed}")

    print(
        f"TOTAL EXECUTION MS : "
        f"{total_execution_time}"
    )

    final_results = {

        "total_tests":
            len(test_cases),

        "passed":
            passed,

        "failed":
            failed,

        "execution_time_ms":
            total_execution_time,

        "results":
            results_summary
    }

    with open(
        "test_results.json",
        "w"
    ) as f:

        json.dump(
            final_results,
            f,
            indent=4
        )

    print(
        "\nResults saved to "
        "test_results.json"
    )

    print(
        "\nClinical Match API "
        "Simulation Completed!"
    )

    print_divider()