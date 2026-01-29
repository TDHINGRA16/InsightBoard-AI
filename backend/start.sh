#!/bin/bash
set -e

echo "Starting InsightBoard AI Backend..."

# Run database migrations
echo "Running database migrations..."

# Start RQ workers in background (2 workers for task processing)
for i in {1..2}; do
    echo "Starting RQ worker $i..."
    rq worker --url $REDIS_URL high default low &
done

# Wait a moment for workers to initialize
sleep 2

echo "Starting FastAPI with Gunicorn..."
# Start FastAPI with Gunicorn (using uvicorn worker class)
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
