#!/bin/bash

# Start the FastAPI application in the background
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Start Celery worker in the background
celery -A utils.celery_app worker --loglevel=info &
CELERY_PID=$!

# Trap SIGTERM and SIGINT
trap "kill $UVICORN_PID $CELERY_PID; exit" SIGTERM SIGINT

# Wait for both processes
wait $UVICORN_PID $CELERY_PID