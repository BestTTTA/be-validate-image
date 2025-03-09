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

# Create a debug script to detect application structure
RUN echo '#!/bin/bash\n\
echo "==== Application Structure ===="\n\
find /app -type f -name "*.py" | sort\n\
\n\
echo "==== Finding Main Application Files ===="\n\
MAIN_FILES=$(find /app -type f -name "main.py" | sort)\n\
if [ -z "$MAIN_FILES" ]; then\n\
  echo "No main.py found!"\n\
else\n\
  echo "Possible main.py files found:"\n\
  for file in $MAIN_FILES; do\n\
    echo " - $file"\n\
    echo "   Content:"\n\
    grep -n "app" $file | head -10\n\
  done\n\
fi\n\
\n\
echo "==== Finding Celery Application Files ===="\n\
CELERY_FILES=$(grep -r "celery" --include="*.py" /app | grep -v "__pycache__" | sort)\n\
if [ -z "$CELERY_FILES" ]; then\n\
  echo "No celery app files found!"\n\
else\n\
  echo "Possible celery app files found:"\n\
  echo "$CELERY_FILES" | head -20\n\
fi\n\
\n\
echo "==== Environment Variables ===="\n\
env | sort\n\
\n\
echo "==== Redis Connection Test ===="\n\
redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping\n\
\n\
echo "==== Python Path ===="\n\
python -c "import sys; print(sys.path)"\n\
\n\
echo "==== Installed Packages ===="\n\
pip list\n\
' > /app/detect_app.sh && chmod +x /app/detect_app.sh

# Create startup script that detects app structure and launches appropriate services
RUN echo '#!/bin/bash\n\
# Run the detection script to find the app structure\n\
/app/detect_app.sh > /app/app_detection.log 2>&1\n\
\n\
# Find main application file\n\
MAIN_PY=$(find /app -type f -name "main.py" | head -1)\n\
if [ -z "$MAIN_PY" ]; then\n\
  echo "No main.py found! Checking for any FastAPI app..."\n\
  FASTAPI_APP=$(grep -r "FastAPI" --include="*.py" /app | grep -v "__pycache__" | head -1 | cut -d ":" -f1)\n\
  if [ -z "$FASTAPI_APP" ]; then\n\
    echo "No FastAPI application found!"\n\
    APP_MODULE="unknown_module"\n\
  else\n\
    APP_DIR=$(dirname "$FASTAPI_APP")\n\
    APP_MODULE=$(echo "$APP_DIR" | sed "s|/app/||g" | tr "/" ".")\n\
    if [ -z "$APP_MODULE" ]; then\n\
      APP_MODULE=$(basename "$FASTAPI_APP" .py)\n\
    else\n\
      APP_MODULE="$APP_MODULE.$(basename "$FASTAPI_APP" .py)"\n\
    fi\n\
  fi\n\
else\n\
  APP_DIR=$(dirname "$MAIN_PY")\n\
  APP_MODULE=$(echo "$APP_DIR" | sed "s|/app/||g" | tr "/" ".")\n\
  if [ -z "$APP_MODULE" ]; then\n\
    APP_MODULE="main"\n\
  else\n\
    APP_MODULE="$APP_MODULE.main"\n\
  fi\n\
fi\n\
echo "Detected FastAPI app module: $APP_MODULE"\n\
\n\
# Find celery application\n\
CELERY_APP=$(grep -r "celery" --include="*.py" /app | grep -v "__pycache__" | grep -i "celery.*=.*Celery" | head -1 | cut -d ":" -f1)\n\
if [ -z "$CELERY_APP" ]; then\n\
  echo "No Celery application found! Trying to find any Celery imports..."\n\
  CELERY_APP=$(grep -r "from celery import" --include="*.py" /app | grep -v "__pycache__" | head -1 | cut -d ":" -f1)\n\
  if [ -z "$CELERY_APP" ]; then\n\
    echo "No Celery imports found!"\n\
    CELERY_MODULE="unknown_module"\n\
  else\n\
    CELERY_DIR=$(dirname "$CELERY_APP")\n\
    CELERY_MODULE=$(echo "$CELERY_DIR" | sed "s|/app/||g" | tr "/" ".")\n\
    if [ -z "$CELERY_MODULE" ]; then\n\
      CELERY_MODULE=$(basename "$CELERY_APP" .py)\n\
    else\n\
      CELERY_MODULE="$CELERY_MODULE.$(basename "$CELERY_APP" .py)"\n\
    fi\n\
  fi\n\
else\n\
  CELERY_DIR=$(dirname "$CELERY_APP")\n\
  CELERY_MODULE=$(echo "$CELERY_DIR" | sed "s|/app/||g" | tr "/" ".")\n\
  if [ -z "$CELERY_MODULE" ]; then\n\
    CELERY_MODULE=$(basename "$CELERY_APP" .py)\n\
  else\n\
    CELERY_MODULE="$CELERY_MODULE.$(basename "$CELERY_APP" .py)"\n\
  fi\n\
fi\n\
echo "Detected Celery app module: $CELERY_MODULE"\n\
\n\
# Generate supervisor configuration\n\
cat > /etc/supervisor/conf.d/app.conf << EOL\n\
[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
logfile_maxbytes=50MB\n\
logfile_backups=10\n\
loglevel=info\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:uvicorn]\n\
command=python -m uvicorn ${APP_MODULE}:app --host 0.0.0.0 --port 8000\n\
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
command=python -m celery -A ${CELERY_MODULE} worker --loglevel=info\n\
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
autorestart=true\n\
EOL\n\
\n\
# Start supervisor\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/app.conf\n\
' > /app/start_app.sh && chmod +x /app/start_app.sh

# Expose the port
EXPOSE 8000

# CMD to run the startup script
CMD ["/app/start_app.sh"]