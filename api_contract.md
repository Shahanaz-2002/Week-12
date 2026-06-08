# 🏥 Clinical Intelligence API Contract (v6.0.0)

## Overview
This document serves as the official API contract for the **Clinical Intelligence & Decision Support Engine**. It defines the RESTful endpoints, request payloads, response structures, and HTTP status codes utilized by the system to provide AI-assisted clinical insights.

---

## 🌐 Global Configurations

* **Base URL:** `http://localhost:8000`
* **Content-Type:** `application/json`
* **CORS Policy:** Allowed `*` (All Origins)

---

## 🩺 Endpoints

### 1. System Health Check
Verifies that the API server is active and running.

* **Method:** `GET`
* **Endpoint:** `/health`
* **Response (200 OK):**
```json
{
  "status": "healthy",
  "api": "Clinical Match API",
  "version": "6.0.0",
  "timestamp": "2026-06-08 12:05:12",
  "server": "FastAPI + Uvicorn"
}