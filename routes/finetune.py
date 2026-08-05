import os
import uuid
import shutil
import zipfile
import threading
import time
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("visioninspect.finetune")
router = APIRouter(prefix="/finetune", tags=["Fine-Tuning"])

# ── In-memory job store ────────────────────────────────────────────────────────
_jobs: dict = {}   # job_id -> JobState dict

UPLOAD_DIR = Path("dataset/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _job(job_id: str) -> dict:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


# ── Models ─────────────────────────────────────────────────────────────────────
class StartTrainingRequest(BaseModel):
    job_id: str
    model_type: str = "yolo"        # "yolo" | "cnn"
    epochs: int = 10
    batch_size: int = 8
    learning_rate: float = 0.001


class ApplyModelRequest(BaseModel):
    job_id: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accept a ZIP of labelled images organised as class folders:
        scratch/img1.jpg, crack/img2.jpg, good/img3.jpg …
    Returns a job_id and a preview of the detected classes.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported.")

    job_id = str(uuid.uuid4())[:8]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    zip_path = job_dir / "dataset.zip"
    with open(zip_path, "wb") as f:
        f.write(await file.read())

    # Extract
    extract_dir = job_dir / "images"
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # Detect classes & image counts
    classes = {}
    for item in extract_dir.rglob("*"):
        if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
            cls_name = item.parent.name.lower()
            classes[cls_name] = classes.get(cls_name, 0) + 1

    if not classes:
        shutil.rmtree(job_dir)
        raise HTTPException(status_code=400, detail="No images found in ZIP. Organise images into class sub-folders.")

    total_images = sum(classes.values())

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "uploaded",
        "dataset_dir": str(extract_dir),
        "classes": classes,
        "total_images": total_images,
        "model_type": None,
        "epochs": None,
        "current_epoch": 0,
        "total_epochs": 0,
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
        "best_accuracy": 0.0,
        "checkpoint_path": None,
        "log": [],
        "started_at": None,
        "finished_at": None,
        "error": None,
    }

    logger.info(f"Dataset uploaded for job {job_id}: {classes}")
    return {"job_id": job_id, "classes": classes, "total_images": total_images}


@router.post("/start")
def start_training(req: StartTrainingRequest, background_tasks: BackgroundTasks):
    """Kick off a background training job."""
    state = _job(req.job_id)
    if state["status"] not in ("uploaded", "failed"):
        raise HTTPException(status_code=400, detail=f"Job is already {state['status']}.")

    state.update({
        "status": "running",
        "model_type": req.model_type,
        "epochs": req.epochs,
        "total_epochs": req.epochs,
        "current_epoch": 0,
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
        "best_accuracy": 0.0,
        "started_at": time.time(),
        "log": [f"Starting {req.model_type.upper()} training — {req.epochs} epochs …"],
        "error": None,
    })

    if req.model_type == "yolo":
        background_tasks.add_task(_run_yolo_finetune, req.job_id, req.epochs, req.batch_size, req.learning_rate)
    else:
        background_tasks.add_task(_run_cnn_finetune, req.job_id, req.epochs, req.batch_size, req.learning_rate)

    return {"job_id": req.job_id, "status": "running"}


@router.get("/status/{job_id}")
def get_status(job_id: str):
    """Poll training progress."""
    state = _job(job_id)
    elapsed = None
    if state["started_at"]:
        end = state["finished_at"] or time.time()
        elapsed = round(end - state["started_at"], 1)
    return {**state, "elapsed_seconds": elapsed}


@router.get("/jobs")
def list_jobs():
    """List all fine-tuning jobs (summary)."""
    summary = []
    for j in _jobs.values():
        summary.append({
            "job_id": j["job_id"],
            "status": j["status"],
            "model_type": j.get("model_type"),
            "best_accuracy": j.get("best_accuracy", 0),
            "total_images": j.get("total_images", 0),
            "classes": list(j.get("classes", {}).keys()),
        })
    return summary


@router.post("/apply")
def apply_model(req: ApplyModelRequest):
    """Copy the fine-tuned checkpoint to the active model path."""
    state = _job(req.job_id)
    if state["status"] != "completed":
        raise HTTPException(status_code=400, detail="Training is not completed yet.")

    checkpoint = state.get("checkpoint_path")
    if not checkpoint or not os.path.exists(checkpoint):
        raise HTTPException(status_code=404, detail="Checkpoint file not found.")

    model_type = state.get("model_type", "cnn")
    if model_type == "yolo":
        dest = "yolov8n_finetuned.pt"
    else:
        dest = os.path.join("models", "active_cnn.pth")
        os.makedirs("models", exist_ok=True)

    shutil.copy2(checkpoint, dest)
    logger.info(f"Applied fine-tuned model from job {req.job_id} → {dest}")
    return {"status": "applied", "model_path": dest, "job_id": req.job_id}


# ── Background training runners ────────────────────────────────────────────────

def _log(job_id: str, msg: str):
    _jobs[job_id]["log"].append(msg)
    logger.info(f"[job:{job_id}] {msg}")


def _run_yolo_finetune(job_id: str, epochs: int, batch_size: int, lr: float):
    state = _jobs[job_id]
    try:
        from ai.yolo_finetune import yolo_finetune
        yolo_finetune(
            job_id=job_id,
            dataset_dir=state["dataset_dir"],
            classes=state["classes"],
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
            state=state,
            log_fn=_log,
        )
    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)
        state["finished_at"] = time.time()
        _log(job_id, f"YOLO training failed: {e}")


def _run_cnn_finetune(job_id: str, epochs: int, batch_size: int, lr: float):
    state = _jobs[job_id]
    try:
        from ai.training import run_training_pipeline_with_progress
        result = run_training_pipeline_with_progress(
            dataset_path=state["dataset_dir"],
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=lr,
            progress_state=state,
            log_fn=_log,
            job_id=job_id,
        )
        state["status"] = "completed"
        state["best_accuracy"] = result.get("best_accuracy", 0)
        state["checkpoint_path"] = result.get("checkpoint_saved")
        state["finished_at"] = time.time()
        _log(job_id, f"CNN training complete. Best val accuracy: {result.get('best_accuracy', 0):.4f}")
    except Exception as e:
        state["status"] = "failed"
        state["error"] = str(e)
        state["finished_at"] = time.time()
        _log(job_id, f"CNN training failed: {e}")
