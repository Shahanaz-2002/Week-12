# API Contract – Clinical Match API

---

# Overview

The Clinical Match API is an AI-powered clinical similarity retrieval system that intelligently analyzes available patient clinical inputs and retrieves the most relevant historical patient cases.

The API supports:
- Dynamic optional field processing
- AI-powered semantic similarity matching
- Clinical recommendation retrieval mapped from historical data and ontologies
- Partial input handling
- Top-K matched patient case retrieval
- Context-aware clinical query generation
- Confidence-based ranking
- Fallback keyword retrieval and response streaming

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
| URL | `/v1/clinical/match` |
| Method | `POST` |
| Content-Type | `application/json` |
| Authentication | `Bearer <token>` (JWT Required) |

---

# 2. Request Schema (Input)

## Description

The API accepts structured or partially structured clinical information. 

**Strict Empty Request Rule:**
While all individual clinical fields are OPTIONAL, a request is considered **invalid and will be rejected** if ALL fields are:
- `null`
- Empty strings (`""`)
- Whitespace-only (`"   "`)

## Request Fields

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
| icd_10_codes | array | No | List of relevant ICD-10 codes |
| snomed_ct_codes | array | No | List of relevant SNOMED CT codes |
| top_k | integer | No | Number of results to return (default: 5, max: 20) |
| stream | boolean | No | Enable streaming response for partial results |

---

# 3. Input Normalization Rules

To ensure high-fidelity AI embeddings and search accuracy, the API automatically applies the following normalizations before processing:
- **Trimming:** All string inputs have leading and trailing spaces removed.
- **Whitespace Reduction:** Multiple sequential spaces are reduced to a single space.
- **Case Normalization:** Standardization applied to specific categorical fields (e.g., gender, affected body parts).
- **Null Conversion:** Empty strings (`""`) are converted to `null`.
- **Type Coercion:** Numeric strings (e.g., `"35"`) are converted to integers where applicable (e.g., `age`).

---

# 4. Example Requests

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
  "doctor_notes": "Possible ligament instability",
  "icd_10_codes": ["M25.561"],
  "top_k": 3
}