#!/bin/bash

# Function to stop processes
cleanup() {
    echo "Stopping processes..."
    kill -TERM "$UVICORN_PID" 2>/dev/null
    kill -TERM "$CELERY_PID" 2>/dev/null
    wait
    exit 0
}

# Setup signal handling
trap cleanup SIGTERM SIGINT

# Start the FastAPI application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Wait for FastAPI to initialize
sleep 5

# Start Celery worker
celery -A utils.celery_app worker --loglevel=info &
CELERY_PID=$!

# Keep the script running and monitor child processes
while kill -0 $UVICORN_PID 2>/dev/null && kill -0 $CELERY_PID 2>/dev/null; do
    sleep 1
done

# If either process dies, cleanup and exit
cleanup