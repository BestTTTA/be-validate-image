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

# Create a default supervisord.conf
RUN mkdir -p /etc/supervisor/conf.d/
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:uvicorn]\n\
command=uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
directory=/app\n\
user=appuser\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/uvicorn.err.log\n\
stdout_logfile=/var/log/supervisor/uvicorn.out.log\n\
startsecs=10\n\
\n\
[program:celery]\n\
command=celery -A face_detection worker --loglevel=info\n\
directory=/app\n\
user=appuser\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/celery.err.log\n\
stdout_logfile=/var/log/supervisor/celery.out.log\n\
startsecs=10\n\
\n\
[program:tail]\n\
command=tail -f /dev/null\n\
user=appuser\n\
autostart=true\n\
autorestart=true' > /etc/supervisor/conf.d/supervisord.conf

# Create directory for supervisor logs
RUN mkdir -p /var/log/supervisor && chown -R appuser:appgroup /var/log/supervisor

# Expose the port
EXPOSE 8000

# CMD to run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]