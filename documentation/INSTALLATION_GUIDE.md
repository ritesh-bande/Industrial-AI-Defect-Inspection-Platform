# Local Installation & Setup Guide

This guide describes how to set up and run the VisionInspect AI console locally on your development system.

---

## 1. Prerequisites

Ensure you have the following installed:
- **Python**: Version 3.10 or 3.11.
- **Node.js**: Version 18 or newer (with npm).
- **PostgreSQL**: Version 14+ (Optional; if absent, system defaults to SQLite fallback).
- **MongoDB**: Version 5+ (Optional; if absent, system defaults to local file logging fallback).

---

## 2. Backend Setup

1. **Clone or enter the project directory**:
   ```bash
   cd VisionInspect_AI
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux/macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install python packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI backend server**:
   ```bash
   uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *Note: On startup, the server automatically creates database tables, seeds a default admin user, and generates mock historical inspection records.*

---

## 3. Frontend Setup

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install Node modules**:
   ```bash
   npm install
   ```

3. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   *The console UI will be accessible at [http://localhost:3000](http://localhost:3000).*

---

## 4. Default Credentials

Use the following seeded credentials to log in:
- **Email**: `admin@visioninspect.ai`
- **Password**: `VisionInspect@Admin2026`
- **Role**: `admin` (Full read/write/configuration privileges)
