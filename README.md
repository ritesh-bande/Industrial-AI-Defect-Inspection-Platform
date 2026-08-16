# VisionInspect AI — Premium Defect Detection Console

VisionInspect AI is an enterprise-grade manufacturing quality control system powered by Computer Vision and AI. It automates product scanning, localizes defect regions, computes severity heatmaps, tracks rework processes, and generates comprehensive factory analytics.

## Features

- **Automated Defect Detection**: AI model (YOLOv8 / CNN / Anomaly Detection) trained to identify anomalies (scratches, cracks, contamination, etc.) in product images.
- **Heatmap & Bounding Box Visualization**: Highlights exact defective regions and computes severity heatmaps.
- **Inspection Dashboard & HUD**: Review inspection results, live camera stream, trends, and history at a glance.
- **Factory Analytics & SPC**: Track defect rates, model performance, and Statistical Process Control metrics over time.
- **Multi-Database Support**: Dual PostgreSQL (relational operational data) & MongoDB (unstructured AI payloads/logs) storage engine.
- **Role-Based Security**: OAuth2 & JWT-authenticated endpoints with role checks (Admin, Engineer, Operator).

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, OAuth2 / JWT Authentication, Bcrypt.
- **Frontend**: Next.js, React.js, Tailwind CSS, Lucide icons, SVG Gauges & Curves.
- **Database**: PostgreSQL (Operational DB) + MongoDB (AI heatmaps, bounding box payloads, logs).
- **AI & Computer Vision**: PyTorch, torchvision, Ultralytics YOLOv8, OpenCV.
- **Containerization & Cloud**: Docker, Docker Compose, Nginx, AWS ECS / Azure Container Apps ready.

## Project Structure

```
VisionInspectAI/
├── frontend/             # Next.js React frontend web console & Dockerfile
│   ├── src/
│   ├── public/
│   └── Dockerfile
├── backend/              # FastAPI server entry point, routes & Dockerfile
│   ├── app/
│   ├── models/
│   ├── requirements.txt
│   └── Dockerfile
├── ai/                   # Model architectures, preprocessing, inference & YOLO wrappers
├── database/             # PostgreSQL and MongoDB client connection helpers
├── models/               # SQLAlchemy models & Pydantic schemas
├── routes/               # FastAPI endpoints (Auth, Inspections, Analytics, Rework, Model)
├── services/             # Core business logic engines
├── docker-compose.yml    # Multi-container local orchestration
├── .env.example          # Template environment variable configurations
├── .gitignore            # Git exclusion rules
└── documentation/        # Extended manuals (Installation, API, Deployment)
```

## Quick Start with Docker Compose

1. Clone repository and create local `.env`:
   ```bash
   cp .env.example .env
   ```

2. Build and start containers:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. Access application services:
   - **Frontend Console**: `http://localhost:3000`
   - **Backend API**: `http://localhost:8000`
   - **Swagger OpenAPI Docs**: `http://localhost:8000/docs`

## Local Development (Without Docker)

### Backend Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate
pip install -r requirements.txt
python backend/main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Documentation & Manuals

1. **[Installation Guide](documentation/INSTALLATION_GUIDE.md)**: Local development setup.
2. **[API Documentation](documentation/API_DOCUMENTATION.md)**: OpenAPI and endpoints reference.
3. **[Deployment Guide](documentation/DEPLOYMENT_GUIDE.md)**: Cloud deployment via Docker and Nginx.
