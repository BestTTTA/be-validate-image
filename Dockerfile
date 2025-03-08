FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpng-dev \
    libjpeg-dev \
    libopenblas-dev \
    supervisor \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash -c "Docker image user" appuser && \
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

# Make start script executable and ensure correct line endings
RUN chmod +x start.sh && \
    sed -i 's/\r$//' start.sh

# Set up supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chown root:root /etc/supervisor/conf.d/supervisord.conf

# Expose the port
EXPOSE 8000

# Switch to root for supervisor (it will launch app processes as appuser)
# CMD to run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]