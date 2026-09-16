#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo -e "${GREEN}🚀 Starting CraftRoom Product Inventory Frontend${NC}"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: node not found. Please install Node.js 18+${NC}"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2)
NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
NODE_MINOR=$(echo $NODE_VERSION | cut -d. -f2)

if [ "$NODE_MAJOR" -lt 18 ]; then
    echo -e "${RED}Error: Node.js 18+ required (found $NODE_VERSION)${NC}"
    exit 1
fi

echo -e "Node.js version: ${GREEN}$NODE_VERSION${NC}"
echo -e "npm version: $(npm -v)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}Dependencies installed${NC}"
else
    # Check if package.json has changed
    if [ -f "package.json" ] && [ -f "package-lock.json" ]; then
        if [ "package.json" -nt "package-lock.json" ]; then
            echo -e "${YELLOW}Dependencies out of sync, reinstalling...${NC}"
            npm install
            echo -e "${GREEN}Dependencies installed${NC}"
        else
            echo -e "Dependencies already installed"
        fi
    fi
fi

# Start the dev server
echo -e "${GREEN}Starting dev server on http://localhost:3000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

npm run dev -- --host 0.0.0.0 --port 3000
