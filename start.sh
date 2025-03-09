#!/bin/bash
# Wait for Redis to be ready
sleep 5

export C_FORCE_ROOT="true"

# Start Celery worker with explicit node name and more options
celery -A utils.celery_app.celery_app worker \
    --loglevel=DEBUG \
    --hostname=worker1@%h \
    --concurrency=2 \
    -Ofair &
CELERY_PID=$!

# Wait longer for Celery to initialize properly
sleep 10

# Check if Celery worker is running and responding
if ps -p $CELERY_PID > /dev/null && celery -A utils.celery_app.celery_app inspect ping; then
    echo "✅ Celery worker started successfully and responding"
else
    echo "❌ Failed to start Celery worker or worker not responding"
    exit 1
fi

# Start FastAPI
python -m uvicorn main:app --host 0.0.0.0 --port 8000