#!/bin/bash
set -e

echo "Starting CraftRoom Backend..."
echo "Database: SQLite"
echo "Host: 0.0.0.0"
echo "Port: 8000"
echo ""

cd /app/backend

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
