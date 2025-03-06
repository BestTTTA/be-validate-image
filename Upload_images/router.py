from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict
import os
import shutil
import uuid
from datetime import datetime
import face_recognition
from minio import Minio
import threading
import time
import pickle
import logging
from utils.face_encoding_manager import load_encodings
from utils.celery_app import celery_app

# MinIO configuration
MINIO_ENDPOINT = "119.59.99.192:9000"
MINIO_ACCESS_KEY = "sut-skin"
MINIO_SECRET_KEY = "sut-skin-2024"
BUCKET_NAME = "test-where-my-images"

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

# Thread-safe lock for updating encodings
encoding_lock = threading.Lock()

# Global dictionary to store face encodings
encodings_data = {
    'face_encodings': [],
    'image_paths': []
}

# Load existing encodings when module is imported
encodings_data = load_encodings()

# Directory and file for storing face encodings
ENCODINGS_DIR = "Encoded_Faces"
ENCODINGS_FILE = os.path.join(ENCODINGS_DIR, "face_encodings.pkl")

def ensure_encodings_dir():
    """Ensure the encodings directory exists."""
    if not os.path.exists(ENCODINGS_DIR):
        os.makedirs(ENCODINGS_DIR)
        print(f"✅ สร้างโฟลเดอร์สำหรับเก็บข้อมูลใบหน้า: {ENCODINGS_DIR}")

def save_encodings(data):
    """Save face encodings to a file."""
    ensure_encodings_dir()
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(data, f)
    print(f"✅ บันทึกข้อมูลใบหน้าสำเร็จ: {len(data['face_encodings'])} ใบหน้า")

@celery_app.task
def process_face_encoding(temp_file_path, unique_filename, original_filename):
    try:
        logger = logging.getLogger('celery')
        logger.info(f"Starting face detection task for {original_filename}")
        
        image = face_recognition.load_image_file(temp_file_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if not face_encodings:
            logger.warning(f"No face detected in {original_filename}")
            return None
        
        logger.info(f"Face detected successfully in {original_filename}")
        
        # Update encodings data with thread safety
        with encoding_lock:
            encodings_data['face_encodings'].append(face_encodings[0])
            encodings_data['image_paths'].append(unique_filename)
            # Save updated encodings
            save_encodings(encodings_data)
            logger.info(f"Face encoding saved for {original_filename}")
            
        return {
            "status": "success",
            "message": f"Face encoding processed for {original_filename}"
        }
    except Exception as e:
        logger.error(f"Error processing face encoding for {original_filename}: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temporary file for {original_filename}")

router = APIRouter(
    prefix="/upload-image",
    tags=["Image Upload"]
)

@router.post("/upload-multiple")
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded")
    
    results = []
    failed = []
    total_files = len(files)
    
    try:
        for file in files:
            temp_file_path = None
            try:
                if not file.content_type.startswith('image/'):
                    failed.append({"filename": file.filename, "error": "Not an image file"})
                    continue
                
                # Create a temporary file
                temp_file_path = f"temp_{uuid.uuid4()}_{file.filename}"
                
                # Read the file content before any operations
                file_content = await file.read()
                
                with open(temp_file_path, "wb") as buffer:
                    buffer.write(file_content)
                
                # Generate unique filename for MinIO
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{uuid.uuid4()}_{file.filename}"
                
                # Upload to MinIO
                minio_client.fput_object(BUCKET_NAME, unique_filename, temp_file_path)
                
                # Start Celery task for face detection and encoding
                task = process_face_encoding.delay(temp_file_path, unique_filename, file.filename)
                
                results.append({
                    "filename": file.filename,
                    "minio_path": unique_filename,
                    "status": "success",
                    "task_id": task.id
                })
                
            except Exception as e:
                failed.append({"filename": file.filename, "error": str(e)})
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            finally:
                await file.close()
        
        # Return final summary
        return {
            "status": "completed",
            "message": "Files uploaded successfully. Face detection and encoding processing in background.",
            "successful_uploads": results,
            "failed_uploads": failed,
            "total_processed": len(results) + len(failed)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))