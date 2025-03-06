from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from typing import List, Dict
from .check_face import check_face
import shutil

router = APIRouter(
    prefix="/check-image",
    tags=["Image Check"]
)

@router.post("/", response_model=Dict[str, object])
async def check_uploaded_image(file: UploadFile = File(...)):
    """Check if the uploaded image matches any faces in the database.
    
    Args:
        file (UploadFile): The uploaded image file
        
    Returns:
        Dict[str, object]: Dictionary containing status and results
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Create a temporary file to store the upload
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the image
        matched_images = check_face(temp_file_path)
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        # If no faces were found in the uploaded image
        if matched_images == "NO_FACE_FOUND":
            return {
                "status": "error",
                "message": "No faces were detected in the uploaded image",
                "matches": []
            }
        
        # If no matches were found but faces were detected
        if not matched_images:
            return {
                "status": "not_found",
                "message": "No matching faces found in the database",
                "matches": []
            }
        
        # If matches were found
        return {
            "status": "success",
            "message": "Matching faces found",
            "matches": matched_images
        }
        
    except Exception as e:
        # Clean up the temporary file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

