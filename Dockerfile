FROM astral/uv:python3.14-trixie

# Install system dependencies including ffmpeg and nginx
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY backend/app ./app
COPY backend/data ./data
COPY config ./config

# Copy frontend static files
COPY frontend/dist ./frontend/dist

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/logs

# Configure nginx
RUN cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80;
    server_name _;

    # Serve frontend static files
    root /app/frontend/dist;
    index index.html;

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy AI image analysis endpoint
    location /ai/ {
        proxy_pass http://127.0.0.1:8000/ai/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROJECT_ROOT=/app

# Expose port 80 for both frontend and backend
EXPOSE 80

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

# Start backend in background
echo "Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

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

# Start nginx
echo "Starting nginx..."
nginx -g 'daemon off;'
EOF

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
