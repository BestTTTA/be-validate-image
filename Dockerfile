FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin -c "Docker image user" appuser && \
    chown -R appuser:appgroup /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chown -R appuser:appgroup /app

# Create directory for face encodings with proper permissions
RUN mkdir -p /app/Encoded_Faces && \
    chown -R appuser:appgroup /app/Encoded_Faces

# Switch to non-root user
USER appuser

# Run the application
CMD ["python","-m","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]