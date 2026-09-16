#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo -e "${GREEN}🚀 Starting CraftRoom Product Inventory Backend${NC}"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# Check for Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "Python version: ${GREEN}$PYTHON_VERSION${NC}"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies if requirements.txt exists and venv is not up to date
if [ -f "requirements.txt" ]; then
    if [ ! -f "venv/.installed" ] || [ "requirements.txt" -nt "venv/.installed" ]; then
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r requirements.txt
        touch venv/.installed
        echo -e "${GREEN}Dependencies installed${NC}"
    else
        echo -e "Dependencies already installed"
    fi
else
    echo -e "${YELLOW}Warning: requirements.txt not found${NC}"
fi

# Check for ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "ffmpeg: ${GREEN}found${NC}"
else
    echo -e "${YELLOW}Warning: ffmpeg not found. Image resizing will be skipped.${NC}"
    echo -e "Install with: sudo pacman -S ffmpeg (Arch) or sudo apt-get install ffmpeg (Ubuntu)"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f "../.env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp "../.env.example" ".env"
    elif [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp ".env.example" ".env"
    fi
fi

# Ensure uploads directory exists
mkdir -p uploads

echo -e "${GREEN}Starting server on http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
