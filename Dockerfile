FROM astral/uv:python3.14-trixie

# Install system dependencies including ffmpeg and Node.js
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies using uv
RUN uv pip install --system -r /app/backend/requirements.txt

# Copy application code
COPY backend/app /app/backend/app
COPY backend/data /app/backend/data
COPY config /app/config

# Copy frontend source and built files
COPY frontend /app/frontend

# Install frontend dependencies
RUN cd /app/frontend && npm install

# Create necessary directories
RUN mkdir -p /app/backend/data/uploads /app/backend/logs

# Copy startup scripts
COPY start-backend.sh /app/start-backend.sh
COPY start-frontend.sh /app/start-frontend.sh

RUN chmod +x /app/start-backend.sh /app/start-frontend.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROJECT_ROOT=/app
ENV FRONTEND_ORIGIN=http://localhost:3000

# Expose ports for both frontend and backend
EXPOSE 3000 8000

# Create main startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "========================================"
echo "  Starting CraftRoom Inventory System"
echo "========================================"
echo ""

# Start backend in background
echo "Starting backend server on port 8000..."
/app/start-backend.sh &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/docs > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to start after 30 seconds"
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo "Starting frontend server on port 3000..."
/app/start-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  CraftRoom is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""

# Wait for any process to exit
wait -n

# Cleanup
exit_code=$?
echo "Shutting down..."
kill $BACKEND_PID 2>/dev/null || true
kill $FRONTEND_PID 2>/dev/null || true
exit $exit_code
EOF

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
