FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev \
    git \  # Add git for installing from GitHub
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install face_recognition_models from GitHub
RUN pip install git+https://github.com/ageitgey/face_recognition_models

# Copy application code
COPY . .

# Run the application
CMD ["python","-m","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]