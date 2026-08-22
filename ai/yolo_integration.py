import os
import cv2
import logging

os.environ["YOLO_OFFLINE"] = "true"
os.environ["ULTRALYTICS_AUTOINSTALL"] = "false"

logger = logging.getLogger("visioninspect.ai")

# Check if ultralytics is available
YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    logger.warning("ultralytics (YOLO) is not available. Using simulated object detection.")

class YOLODetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.getenv("MODEL_PATH", "yolov8n.pt")
        self.model_path = model_path
        self.model = None

    def _ensure_model_loaded(self):
        if self.model is None and YOLO_AVAILABLE:
            try:
                self.model = YOLO(self.model_path)
                logger.info(f"YOLO model loaded successfully from {self.model_path}.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}. Falling back to simulation.")
                self.model = None

    # Industrial defect labels that are valid detections.
    # Generic COCO classes (toilet, person, bottle etc.) are NOT valid defects.
    DEFECT_LABELS = {
        "scratch", "crack", "dent", "missing_component", "surface_damage",
        "misalignment", "deformation", "corrosion", "contamination", "burr",
        "chip", "fracture", "hole", "stain", "defect", "anomaly", "broken",
        "damage", "fault", "flaw", "imperfection", "irregularity"
    }
    # Minimum confidence to accept a detection (raised from 0.25 to filter noise)
    MIN_CONFIDENCE = 0.50

    def detect(self, image_path: str, confidence_threshold=None) -> list:
        """
        Runs YOLO object detection.
        Returns only industrial defect detections above confidence threshold.
        Returns:
            list of dicts: [ { "box": [xmin, ymin, xmax, ymax], "label": str, "score": float } ]
        """
        threshold = confidence_threshold if confidence_threshold is not None else self.MIN_CONFIDENCE

        self._ensure_model_loaded()

        if not YOLO_AVAILABLE or self.model is None:
            return self._simulate_detection(image_path)

        try:
            results = self.model(image_path, verbose=False)
        except Exception as e:
            logger.error(f"YOLO model execution error: {e}. Falling back to simulation.")
            return self._simulate_detection(image_path)
            
        try:
            detections = []
            if not results:
                return detections
                
            result = results[0]
            boxes = result.boxes
            
            for box in boxes:
                # Get coordinates
                coords = box.xyxy[0].cpu().numpy().tolist()  # [xmin, ymin, xmax, ymax]
                score = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                
                # Retrieve label name from YOLO class names map
                label = result.names.get(cls_id, f"class_{cls_id}").lower()
                
                # Only accept detections that are:
                # 1. Above the minimum confidence threshold
                # 2. A known industrial defect label (filter out COCO objects like toilet, person, etc.)
                if score >= threshold and label in self.DEFECT_LABELS:
                    detections.append({
                        "box": [int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])],
                        "label": label,
                        "score": round(score, 4)
                    })
            return detections
        except Exception as e:
            logger.error(f"Error executing YOLO detection: {e}")
            return self._simulate_detection(image_path)

    def _simulate_detection(self, image_path: str) -> list:
        """
        Fallback simulation return empty detections list so main CV engine analyzes pixels.
        """
        return []
