FROM astral/uv:python3.14-trixie

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
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

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROJECT_ROOT=/app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
