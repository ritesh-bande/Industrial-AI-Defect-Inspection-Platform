import os
import json
import logging
from pymongo import MongoClient

logger = logging.getLogger("visioninspect.database")

# Primary MongoDB Connection URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "visioninspect")

# Local Mock directory fallback
LOCAL_MOCK_DIR = os.path.join("static", "uploads", "mongodb_mock")

db_client = None
mongo_db = None
is_mock = False

try:
    db_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    # Test connection
    db_client.server_info()
    mongo_db = db_client[MONGO_DB_NAME]
    logger.info("MongoDB connection established successfully.")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}. Using local JSON files as fallback.")
    is_mock = True
    os.makedirs(LOCAL_MOCK_DIR, exist_ok=True)

def get_mongo_db():
    """Returns the MongoDB database instance or None if mocking"""
    if is_mock:
        return None
    return mongo_db

def save_unstructured_metadata(inspection_id: int, data: dict) -> str:
    """
    Saves unstructured AI metadata (bounding boxes, logs, raw heatmap float coordinates).
    Returns a string reference identifier.
    """
    data_with_id = {"inspection_id": inspection_id, **data}
    
    if is_mock:
        # Save to local JSON files
        file_path = os.path.join(LOCAL_MOCK_DIR, f"meta_{inspection_id}.json")
        try:
            with open(file_path, "w") as f:
                json.dump(data_with_id, f, indent=2, default=str)
            return f"local_file://{file_path}"
        except Exception as e:
            logger.error(f"Failed to write mock MongoDB metadata: {e}")
            return "error_local"
    else:
        try:
            collection = mongo_db["inspection_metadata"]
            # Upsert by inspection_id
            result = collection.update_one(
                {"inspection_id": inspection_id},
                {"$set": data_with_id},
                upsert=True
            )
            if result.upserted_id:
                return str(result.upserted_id)
            return f"mongo_id_{inspection_id}"
        except Exception as e:
            logger.error(f"Failed to write MongoDB metadata: {e}")
            return "error_mongo"

def get_unstructured_metadata(inspection_id: int) -> dict:
    """
    Retrieves unstructured AI metadata by inspection_id.
    """
    if is_mock:
        file_path = os.path.join(LOCAL_MOCK_DIR, f"meta_{inspection_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read mock MongoDB metadata: {e}")
        return {}
    else:
        try:
            collection = mongo_db["inspection_metadata"]
            doc = collection.find_one({"inspection_id": inspection_id})
            if doc:
                doc["_id"] = str(doc["_id"])  # serialize ObjectId
                return doc
        except Exception as e:
            logger.error(f"Failed to read MongoDB metadata: {e}")
        return {}
