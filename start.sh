#!/bin/bash
# Start the FastAPI application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to start
sleep 5

# Start Celery worker
celery -A utils.celery_app worker --loglevel=info

# Keep the container running
wait