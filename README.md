# VisionInspectAI

AI-powered visual inspection system for automated defect detection in manufacturing. VisionInspectAI uses computer vision and deep learning to identify anomalies in product images, helping quality control teams catch defects faster and more consistently than manual inspection.

## Features

- **Automated Defect Detection** — AI model trained to identify anomalies (scratches, cracks, contamination, etc.) in product images
- **Heatmap Visualization** — Highlights the exact regions of an image flagged as defective
- **Inspection Dashboard** — Review inspection results, trends, and history at a glance
- **Analytics** — Track defect rates, model performance, and inspection metrics over time
- **Camera Integration** — Capture images directly for real-time inspection
- **User Authentication** — Secure login with role-based access (e.g. admin, inspector)
- **Model Metrics** — Monitor and evaluate AI model accuracy and performance

## Tech Stack

**Backend**
- FastAPI (Python)
- SQLite (via SQLAlchemy)
- OAuth2 password-based authentication
- PyTorch / TensorFlow *(update with whichever your `ai_model.py` uses)*

**Frontend**
- Next.js (React)
- TypeScript

**Dataset**
- [MVTec Anomaly Detection Dataset](https://www.mvtec.com/company/research/datasets/mvtec-ad) — used for training/evaluating the anomaly detection model (not included in this repo due to size; see [Dataset Setup](#dataset-setup))

## Project Structure

```
VisionInspect_AI/
├── backend/
│   ├── main.py          # FastAPI app entry point, routes, auth
│   ├── ai_model.py       # Model loading and inference logic
│   ├── database.py       # DB connection and session handling
│   ├── security.py       # Password hashing, JWT/auth utilities
│   └── static/           # Uploaded images and generated heatmaps
├── frontend/
│   └── src/app/
│       ├── analytics/
│       ├── camera/
│       ├── dashboard/
│       ├── inspection/
│       ├── login/
│       └── model-metrics/
├── dataset/               # MVTec AD dataset (not tracked in git — see below)
└── milestone_1/           # Milestone 1 deliverables
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
python main.py
```

The backend will start on `http://localhost:8000` by default.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:3000` by default.

### Environment Variables

Create a `.env.local` file inside `frontend/` with the required variables (not committed to git for security reasons):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

*(Add any other required keys here.)*

## Dataset Setup

The MVTec AD dataset (~4–5 GB) is **not included** in this repository due to size. To set it up locally:

1. Download the dataset from the [official MVTec AD page](https://www.mvtec.com/company/research/datasets/mvtec-ad)
2. Extract it into the `dataset/mvtec_anomaly_detection/` folder at the project root
3. Ensure the folder structure matches what `ai_model.py` expects (per-category subfolders: `bottle/`, `cable/`, `capsule/`, etc.)

## Usage

1. Start both the backend and frontend servers (see above)
2. Navigate to `http://localhost:3000` in your browser
3. Log in with your credentials
4. Upload or capture an image for inspection
5. View results, heatmaps, and analytics on the dashboard

## Branch Info

This project uses per-contributor branches. Changes should be pushed to your own branch and merged into `main` via pull request after review — not pushed directly to `main`.

## Contributing

1. Create or switch to your own branch
2. Make your changes
3. Commit with a clear message
4. Push to your branch
5. Open a pull request into `main` for review

## License

*(Add license details here.)*
