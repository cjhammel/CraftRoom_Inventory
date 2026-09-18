#!/bin/bash
set -e

echo "Starting CraftRoom Frontend..."
echo "Host: 0.0.0.0"
echo "Port: 3000"
echo ""

cd /app/frontend

# Start vite dev server
exec npx vite --host 0.0.0.0 --port 3000
