# Swagger & API Documentation

FastAPI automatically generates an interactive Swagger interface. Once the backend is running, visit:
- **Interactive UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 1. Authentication Router
Endpoints for logging in and validating JWT tokens.

### `POST /api/auth/register`
Creates a new user.
- **Request Body**:
  ```json
  {
    "username": "operator_name",
    "email": "operator@factory.com",
    "password": "securepassword",
    "role": "operator"
  }
  ```
- **Response (201)**: Returns JWT bearer token.

### `POST /api/auth/login`
Logs in a user.
- **Request Body**:
  ```json
  {
    "email": "admin@visioninspect.ai",
    "password": "VisionInspect@Admin2026"
  }
  ```

### `GET /api/auth/me`
Returns current user parameters. Requires header `Authorization: Bearer <token>`.

---

## 2. Inspections Router
Endpoints for product scanning and review.

### `POST /api/inspections/inspect`
Uploads and scans a single image using the active AI pipeline (YOLO or PyTorch CNN).
- **Multipart Form Data**:
  - `file`: Image file (PNG/JPG).
  - `product_id`: `bottle` | `cable` | `tile` | `leather`
  - `production_line`: `line_1` | `line_2`
  - `batch_number`: `string`

### `POST /api/inspections/batch-inspect`
Uploads multiple images and returns a list of inspection records.

### `PATCH /api/inspections/{id}/review-status`
Updates operator verification decision.
- **Request Body**:
  ```json
  {
    "review_status": "approved" | "rejected" | "sent_for_rework",
    "review_notes": "Surface scratch repaired."
  }
  ```

---

## 3. Analytics Router
Endpoints for factory statistics.

### `GET /api/analytics/summary`
Yield rates, defect composition, and trend lines.

### `GET /api/analytics`
Detailed evaluation metrics including confusion matrix cells, ROC curves, PR curves, and memory usage.

### `GET /api/analytics/export.csv`
Downloads inspection data as CSV format.
