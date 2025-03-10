from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Add this import
import face_recognition
import numpy as np
import os
import shutil
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_URL = "sqlite:///./faces.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FaceData(Base):
    __tablename__ = "faces"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)
    encoding = Column(String)

Base.metadata.create_all(bind=engine)

IMAGE_DIR = "stored_faces"
os.makedirs(IMAGE_DIR, exist_ok=True)

def encode_face(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None

@app.post("/upload/")
async def upload_face(files: list[UploadFile]):  
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    results = []
    
    for file in files:
        try:
            if not file.content_type.startswith('image/'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Invalid file type. Only images are allowed."
                })
                continue

            file_location = f"{IMAGE_DIR}/{file.filename}"
            
            contents = await file.read()
            
            with open(file_location, "wb") as buffer:
                buffer.write(contents)

            encoding = encode_face(file_location)
            if encoding is None:
                os.remove(file_location)
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "No face detected!"
                })
                continue

            db = SessionLocal()
            db_face = FaceData(file_path=file_location, encoding=str(encoding.tolist()))
            db.add(db_face)
            db.commit()
            db.close()

            results.append({
                "filename": file.filename,
                "status": "success",
                "message": "Face stored successfully",
                "file_path": file_location
            })

        except Exception as e:
            if 'file_location' in locals() and os.path.exists(file_location):
                os.remove(file_location)
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
            
        finally:
            await file.seek(0)

    return {"results": results}

import base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

@app.post("/search/")
async def search_face(file: UploadFile = File(...)):
    temp_path = f"{IMAGE_DIR}/temp.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    search_encoding = encode_face(temp_path)
    if search_encoding is None:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="No face detected in uploaded image!")

    db = SessionLocal()
    faces = db.query(FaceData).all()
    db.close()

    matched_images = []
    for face in faces:
        stored_encoding = np.array(eval(face.encoding))
        match = face_recognition.compare_faces([stored_encoding], search_encoding, tolerance=0.2)
        if match[0]:
            try:
                base64_img = image_to_base64(face.file_path)
                matched_images.append(base64_img)
            except Exception as e:
                print(f"Error converting image to base64: {str(e)}")
                continue

    os.remove(temp_path)
    return {"matched_images": matched_images}
