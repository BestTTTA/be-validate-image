#!/bin/bash
# Wait for Redis to be ready
sleep 10

export C_FORCE_ROOT="true"

# Set Celery broker URL explicitly
export CELERY_BROKER_URL="redis://redis:6379/0"
export CELERY_RESULT_BACKEND="redis://redis:6379/0"

# Start Celery worker with explicit node name and more options
celery -A utils.celery_app.celery_app worker \
    --loglevel=DEBUG \
    --hostname=worker1@%h \
    --concurrency=2 \
    -Ofair \
    --without-heartbeat \
    --without-mingle &
CELERY_PID=$!

# Wait longer for Celery to initialize properly
sleep 45

# Try multiple times to check if Celery is responding
max_retries=5
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if ps -p $CELERY_PID > /dev/null && celery -A utils.celery_app.celery_app inspect ping; then
        echo "✅ Celery worker started successfully and responding"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            echo "Retry $retry_count: Waiting for Celery worker to respond..."
            sleep 15
        fi
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Failed to start Celery worker or worker not responding after $max_retries attempts"
    exit 1
fi

# Start FastAPI
python -m uvicorn main:app --host 0.0.0.0 --port 8000