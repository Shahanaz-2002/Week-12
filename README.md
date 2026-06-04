# 🏥 Clinical Match API

---

# 📌 Project Overview

The Clinical Match API is an AI-powered clinical similarity matching and recommendation system designed to intelligently analyze patient clinical inputs and retrieve the most relevant historical patient cases.

The system dynamically processes available patient information and performs semantic similarity matching using transformer-based embeddings and cosine similarity retrieval techniques.

The API is designed to support:
- AI-assisted clinical recommendations
- Clinical decision support systems
- Patient similarity analysis
- Intelligent healthcare assistance pipelines

---

# 🎯 Core Features

The Clinical Match API provides:

✅ Dynamic optional field processing

✅ AI-powered semantic similarity matching

✅ Intelligent clinical context generation

✅ Top 2 similar patient case retrieval

✅ Recommended tests and medicines

✅ Confidence score generation

✅ Human-readable AI explanations

✅ Partial input handling

---

# 🧠 How the AI Works

The system processes patient inputs through multiple AI stages.

---

## 1. Clinical Context Generation

Available clinical fields are dynamically combined into a meaningful clinical summary.

### Example

Input:

```json
{
  "chief_complaint": "Right knee pain",
  "occupation": "Construction Worker",
  "age": 35
}
```

Generated Clinical Context:

```text
35 year old construction worker presenting with right knee pain.
```

---

## 2. Vector Embedding Generation

The generated clinical context is converted into vector embeddings using transformer-based NLP models.

Recommended embedding models:
- Sentence Transformers
- BioClinicalBERT
- BioBERT

---

## 3. Similarity Retrieval

The system compares the patient embedding against historical patient embeddings using:

### Cosine Similarity

```text
Higher similarity score → More clinically relevant match
```

---

## 4. Recommendation Generation

The top matched patient cases are analyzed to retrieve:
- Recommended tests
- Recommended medicines
- Doctor notes
- Similar clinical observations

---

# 📂 Project Structure

Organize the project files as follows:

```text
clinical_match_api/
│
├── api/
│   └── main.py
│
├── models/
│   └── models.py
│
├── services/
│   ├── clinical_match_service.py
│   └── context_builder.py
│
├── retrieval/
│   ├── database.py
│   ├── embedding.py
│   ├── embedding_store.py
│   └── retrieval_engine.py
│
├── insight/
│   ├── confidence_engine.py
│   ├── insight_aggregator.py
│   └── explanation_generator.py
│
├── datasets/
│   └── patient_cases.json
│
├── tests/
│   └── test_api_simulation.py
│
├── exports/
│   └── postman_collection.json
│
├── api_contract.md
├── requirements.txt
├── README.md
├── config.py
└── utils.py
```

---

# 🛠️ Setup and Installation

# 1. Prerequisites

Ensure the following are installed:

- Python 3.10+
- MongoDB (optional for database storage)
- pip
- Virtual environment (recommended)

---

# 2. Install Dependencies

Open terminal inside the project root directory.

Run:

```bash
pip install -r requirements.txt
```

---

# 3. Dataset Preparation

Historical patient cases are required for similarity matching.

You can:
- Use JSON datasets
- Use MongoDB
- Generate synthetic patient cases

---

## Example Dataset Entry

```json
{
  "case_id": "CASE_001",

  "chief_complaint": "Lower back pain",

  "affected_body_part": "Lower Back",

  "recommended_tests": [
    "MRI"
  ],

  "recommended_medicines": [
    "Ibuprofen"
  ]
}
```

---

# 4. Generate Embeddings

Before similarity matching, embeddings must be generated for historical patient cases.

Run:

```bash
python -m retrieval.embedding_store
```

This creates vector embeddings for all stored patient records.

---

# 🚀 Running the API

# Step 1 — Start the Server

Run:

```bash
python -m api.main
```

---

# API URLs

| Service | URL |
|---|---|
| API Base URL | http://localhost:8000 |
| Swagger Documentation | http://localhost:8000/docs |
| ReDoc Documentation | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

# Step 2 — Send API Request

You can test the API using:
- Postman
- Swagger UI
- Insomnia
- curl
- Automated test scripts

---

# 📥 Example API Request

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

  "subjective_assessment":
    "Pain increases during movement",

  "functional_assessment":
    "Difficulty squatting",

  "physical_examination":
    "Swelling near patella",

  "objective_findings":
    "Reduced range of motion",

  "patient_pain_classification":
    "Moderate"
}
```

---

# 📤 Example API Response

```json
{
  "status": "success",

  "message":
    "Top matching patient cases retrieved successfully",

  "matches": [
    {
      "case_id": "CASE_102",

      "match_score": 0.91,

      "chief_complaint":
        "Knee pain during walking",

      "affected_body_part":
        "Right Knee",

      "recommended_tests": [
        "MRI",
        "X-Ray"
      ],

      "recommended_medicines": [
        "Ibuprofen",
        "Muscle Relaxant"
      ],

      "doctor_notes":
        "Possible ligament strain with inflammation"
    }
  ],

  "confidence_score": 0.89,

  "generated_clinical_context":
    "35 year old male construction worker presenting with right knee pain.",

  "explanation":
    "Matches were retrieved using semantic similarity analysis."
}
```

---

# 🧪 Automated API Testing

To test:
- API stability
- Validation handling
- Partial inputs
- Edge cases

Run:

```bash
python tests/test_api_simulation.py
```

---

# ✅ Supported Test Cases

The automated test script validates:

| Test Scenario | Purpose |
|---|---|
| Full Input | Complete clinical request |
| Partial Input | Missing optional fields |
| Single Field Input | Minimal clinical data |
| Invalid Age | Validation testing |
| Empty Request | Error handling |
| Long Input | Stress testing |
| Null Fields | Optional field validation |

---

# ⚠️ Error Handling

# 1. Empty Request Error

Triggered when no clinical fields are provided.

```json
{
  "detail": {
    "error": "Invalid Input",
    "message": "At least one clinical field is required"
  }
}
```

---

# 2. Validation Error

Triggered when invalid field values are provided.

Example:
- age > 120
- invalid data type

---

# 3. No Similar Cases Found

Triggered when no matching patient cases exist.

```json
{
  "detail": {
    "error": "No Results",
    "message": "No similar patient cases found"
  }
}
```

---

# 4. Internal Server Error

Triggered when:
- model loading fails
- embedding generation fails
- database connection fails

```json
{
  "detail": {
    "error": "Internal Server Error",
    "message": "Error occurred while processing clinical request"
  }
}
```

---

# 📊 AI Similarity Pipeline

```text
Patient Clinical Input
            ↓
Dynamic Context Builder
            ↓
Transformer Embedding Model
            ↓
Vector Embedding
            ↓
Cosine Similarity Search
            ↓
Top Matching Cases
            ↓
Recommendation Generation
            ↓
Final API Response
```

---

# 🧰 Technology Stack

| Component | Technology |
|---|---|
| Backend Framework | FastAPI |
| AI Embeddings | Sentence Transformers |
| Similarity Engine | Cosine Similarity |
| Validation | Pydantic |
| API Documentation | Swagger UI |
| Testing | Postman |
| Programming Language | Python |

---

# 📈 Future Enhancements

Planned future improvements include:

- FAISS vector similarity search
- BioClinicalBERT integration
- Multi-patient recommendation ranking
- Clinical risk scoring
- Real-time database retrieval
- Recommendation explainability engine
- Medical ontology integration
- Multi-specialty support
- Temporal patient tracking

---

# 👩‍⚕️ Clinical Match API Goals

The long-term goal of this system is to provide:
- Faster clinical decision assistance
- AI-supported patient analysis
- Intelligent healthcare retrieval systems
- Scalable medical recommendation architectures

---

# 📄 License

This project is intended for:
- Research
- Educational purposes
- AI healthcare experimentation
- Clinical recommendation system development

---