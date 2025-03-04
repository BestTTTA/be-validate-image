from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Check_image.router import router as check_image_router

app = FastAPI(
    title="Face Recognition API",
    description="API for checking and comparing face images",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the check image router
app.include_router(check_image_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)