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
    redis-tools \
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

# Create directories for logs
RUN mkdir -p /var/log/supervisor && \
    mkdir -p /app/logs && \
    chown -R appuser:appgroup /var/log/supervisor && \
    chown -R appuser:appgroup /app/logs

# Create a debug script to verify application structure
RUN echo '#!/bin/bash\n\
echo "==== Application Structure ===="\n\
find /app -type f -name "*.py" | sort\n\
echo "==== Environment Variables ===="\n\
env | sort\n\
echo "==== Redis Connection Test ===="\n\
redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping\n\
echo "==== Python Version ===="\n\
python --version\n\
echo "==== Installed Packages ===="\n\
pip list\n\
' > /app/debug.sh && chmod +x /app/debug.sh

# Create a proper supervisord.conf
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
logfile_maxbytes=50MB\n\
logfile_backups=10\n\
loglevel=info\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:debug]\n\
command=/app/debug.sh\n\
user=appuser\n\
autostart=true\n\
autorestart=false\n\
startretries=0\n\
stdout_logfile=/var/log/supervisor/debug.log\n\
stderr_logfile=/var/log/supervisor/debug.err.log\n\
\n\
[program:uvicorn]\n\
command=python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
directory=/app\n\
user=appuser\n\
autostart=true\n\
autorestart=true\n\
startretries=3\n\
stderr_logfile=/var/log/supervisor/uvicorn.err.log\n\
stdout_logfile=/var/log/supervisor/uvicorn.out.log\n\
redirect_stderr=true\n\
startsecs=5\n\
\n\
[program:celery]\n\
command=python -m celery -A face_detection worker --loglevel=info\n\
directory=/app\n\
user=appuser\n\
autostart=true\n\
autorestart=true\n\
startretries=3\n\
stderr_logfile=/var/log/supervisor/celery.err.log\n\
stdout_logfile=/var/log/supervisor/celery.out.log\n\
redirect_stderr=true\n\
startsecs=5\n\
\n\
[program:tail]\n\
command=tail -f /dev/null\n\
user=appuser\n\
autostart=true\n\
autorestart=true' > /etc/supervisor/conf.d/supervisord.conf

# Expose the port
EXPOSE 8000

# CMD to run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]