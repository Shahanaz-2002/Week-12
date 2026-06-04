# API Contract – Clinical Match API

---

# Overview

The Clinical Match API is an AI-powered clinical similarity retrieval system that intelligently analyzes available patient clinical inputs and retrieves the most relevant historical patient cases.

The API supports:

- Dynamic optional field processing
- AI-powered semantic similarity matching
- Clinical recommendation retrieval
- Partial input handling
- Top-N matched patient case retrieval
- Context-aware clinical query generation
- Confidence-based ranking

This API is designed as a foundational module for:

- AI-assisted clinical recommendations
- Patient case similarity search
- Clinical decision support systems
- Intelligent healthcare assistance pipelines
- Retrieval-Augmented Clinical Systems (RAG)

---

# 1. Endpoint Details

| Property | Value |
|---|---|
| URL | `/clinical/match` |
| Method | `POST` |
| Content-Type | `application/json` |

---

# 2. Request Schema (Input)

## Description

The API accepts structured or partially structured clinical information.

IMPORTANT:

- All fields are OPTIONAL
- The API dynamically processes only the available inputs
- Semantic retrieval works even with partial information
- Empty requests are rejected

---

# Request Fields

| Field Name | Type | Required | Description |
|---|---|---|---|
| chief_complaint | string | No | Primary complaint reported by patient |
| affected_body_part | string | No | Affected body region |
| symptoms_duration | string | No | Duration of symptoms |
| previous_injuries | string | No | Injury or trauma history |
| current_medications | string | No | Current medications |
| allergies | string | No | Known allergies |
| occupation | string | No | Patient occupation |
| activity_levels | string | No | Physical activity level |
| gender | string | No | Patient gender |
| age | integer | No | Patient age |
| doctor_name | string | No | Clinician or doctor name |
| subjective_assessment | string | No | Subjective assessment notes |
| functional_assessment | string | No | Functional limitations |
| physical_examination | string | No | Physical examination findings |
| objective_findings | string | No | Objective clinical findings |
| patient_pain_classification | string | No | Pain severity classification |
| symptoms | string | No | Combined symptom description |
| doctor_notes | string | No | Additional clinician notes |
| clinical_history | string | No | Historical clinical background |

---

# 3. Example Requests

---

## Full Clinical Input

```json
{
  "chief_complaint": "Right knee pain while climbing stairs",
  "affected_body_part": "Right Knee",
  "symptoms_duration": "3 weeks",
  "previous_injuries": "ACL tear 2 years ago",
  "current_medications": "Ibuprofen",
  "allergies": "Penicillin",
  "occupation": "Construction Worker",
  "activity_levels": "High",
  "gender": "Male",
  "age": 35,
  "doctor_name": "Dr Kumar",
  "subjective_assessment": "Pain increases during movement",
  "functional_assessment": "Difficulty squatting",
  "physical_examination": "Swelling near patella",
  "objective_findings": "Reduced range of motion",
  "patient_pain_classification": "Moderate",
  "doctor_notes": "Possible ligament instability"
}
```

---

## Partial Input Example

```json
{
  "chief_complaint": "Lower back pain",
  "occupation": "Driver",
  "age": 45
}
```

---

## Minimal Input Example

```json
{
  "chief_complaint": "Shoulder stiffness"
}
```

---

## Dynamic Optional Input Example

```json
{
  "symptoms": "Swelling and tenderness",
  "doctor_notes": "Suspected inflammation",
  "clinical_history": "Previous sports injury"
}
```

---

# 4. Response Schema (Output)

## Description

The API returns:

- Top matched historical patient cases
- Similarity scores
- Recommended diagnostic tests
- Recommended medicines
- AI-generated clinical context
- Confidence score
- Explanation of retrieval process
- Processing metadata

---

# Response Fields

| Field Name | Type | Description |
|---|---|---|
| status | string | API response status |
| message | string | API response message |
| request_id | string | Unique request identifier |
| matches | array | Top matched patient cases |
| total_matches_found | integer | Number of matched cases returned |
| confidence_score | float | Overall confidence score |
| generated_context | string | Dynamically generated clinical context |
| search_query | string | Generated semantic retrieval query |
| processing_time_ms | float | API processing time |
| explanation | string | Explanation of similarity generation |

---

# Match Object Fields

| Field Name | Type | Description |
|---|---|---|
| case_id | string | Historical patient case ID |
| match_score | float | Similarity score between 0 and 1 |
| confidence_level | string | Match confidence category |
| chief_complaint | string | Complaint from matched case |
| affected_body_part | string | Body part from matched case |
| recommended_tests | array | Suggested diagnostic tests |
| recommended_medicines | array | Suggested medicines |
| doctor_notes | string | Additional clinician notes |
| similarity_reason | string | Explanation for similarity |

---

# 5. Example Success Response

```json
{
  "status": "success",
  "message": "Top matching patient cases retrieved successfully",

  "request_id": "REQ-91F3ACD2",

  "matches": [
    {
      "case_id": "CASE_102",

      "match_score": 0.91,

      "confidence_level": "High",

      "chief_complaint": "Knee pain during walking",

      "affected_body_part": "Right Knee",

      "recommended_tests": [
        "MRI",
        "X-Ray"
      ],

      "recommended_medicines": [
        "Ibuprofen",
        "Muscle Relaxant"
      ],

      "doctor_notes":
        "Possible ligament strain with inflammation",

      "similarity_reason":
        "Matched based on knee pain, swelling and previous injury history"
    },

    {
      "case_id": "CASE_045",

      "match_score": 0.87,

      "confidence_level": "High",

      "chief_complaint": "Patellar discomfort",

      "affected_body_part": "Knee",

      "recommended_tests": [
        "CT Scan"
      ],

      "recommended_medicines": [
        "Paracetamol"
      ],

      "doctor_notes":
        "Observe swelling progression",

      "similarity_reason":
        "Matched based on pain location and movement restriction"
    }
  ],

  "total_matches_found": 2,

  "confidence_score": 0.89,

  "generated_context":
    "35 year old male construction worker presenting with right knee pain while climbing stairs with previous ACL injury history.",

  "search_query":
    "Right knee pain | swelling near patella | reduced range of motion",

  "processing_time_ms": 128.42,

  "explanation":
    "Matches were retrieved using AI-based semantic similarity analysis on available clinical inputs."
}
```

---

# 6. Validation Rules

| Validation Rule | Description |
|---|---|
| At least one field required | Empty request not allowed |
| age range | Must be between 0 and 120 |
| gender validation | Male, Female, Other, Prefer Not To Say |
| Optional fields | Empty values handled safely |
| Null values | Automatically cleaned |
| Semantic processing | Works with partial input |
| Text normalization | Extra spaces automatically removed |
| Similarity scoring | Scores normalized between 0 and 1 |

---

# 7. Error Handling

---

## Validation Error Example

```json
{
  "detail": {
    "error": "Invalid Input",
    "message": "At least one clinical field is required"
  }
}
```

---

## Invalid Age Example

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "age"
      ],
      "msg": "Input should be less than or equal to 120"
    }
  ]
}
```

---

## Invalid Gender Example

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": [
        "body",
        "gender"
      ],
      "msg": "Gender must be Male, Female, Other or Prefer Not To Say"
    }
  ]
}
```

---

## No Similar Cases Found

```json
{
  "detail": {
    "error": "No Results",
    "message": "No similar patient cases found",
    "matches": [],
    "confidence_score": 0.0
  }
}
```

---

## Internal Server Error

```json
{
  "detail": {
    "error": "Internal Server Error",
    "message": "Error occurred while processing clinical request"
  }
}
```

---

# 8. Health Check Endpoint

| Property | Value |
|---|---|
| URL | `/health` |
| Method | `GET` |

---

## Example Response

```json
{
  "status": "Clinical Match API is running"
}
```

---

# 9. Swagger Documentation

FastAPI automatically generates Swagger documentation.

| URL | Purpose |
|---|---|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc Documentation |

---

# 10. Core Pipeline Workflow

The API internally performs:

1. Input Validation
2. Dynamic Input Cleaning
3. Clinical Context Generation
4. Semantic Search Query Construction
5. Embedding Generation
6. Similarity Retrieval
7. Confidence Calculation
8. Recommendation Aggregation
9. Final Response Formatting

---

# 11. Future Enhancements

Planned improvements include:

- FAISS vector similarity search
- BioClinicalBERT integration
- Real-time database retrieval
- Multi-patient recommendation ranking
- Explainable AI modules
- Clinical risk prediction
- Ontology-aware retrieval
- ICD code integration
- SNOMED CT integration
- Multilingual clinical retrieval
- GPU embedding acceleration

---

# 12. Technology Stack

| Component | Technology |
|---|---|
| Backend Framework | FastAPI |
| AI Embeddings | Sentence Transformers / BioBERT |
| Similarity Engine | Cosine Similarity |
| Validation | Pydantic V2 |
| API Documentation | Swagger UI |
| Testing | Postman / Python Simulation |
| Language | Python |
| Vector Processing | NumPy |
| Logging | Python Logging |

---

# 13. API Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Invalid Input |
| 404 | No Similar Cases Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

# 14. Security Recommendations

Recommended production security practices:

- HTTPS enforcement
- JWT authentication
- API rate limiting
- Request payload validation
- Audit logging
- PHI masking
- Secure database storage
- Input sanitization

---

# 15. Performance Recommendations

Recommended optimizations:

- Vector database indexing
- FAISS retrieval acceleration
- Embedding caching
- Async API processing
- GPU embedding inference
- Batch retrieval optimization

---