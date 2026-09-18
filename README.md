# CraftRoom Product Inventory

A lightweight web application to inventory craft stamps. Built with FastAPI (backend) and React + Vite (frontend).

## Features

- **CRUD operations** — Create, view, edit, and delete stamps
- **Search & filter** — Search by name/brand/item, filter by brand, product type, theme, location, and sentiments
- **Image uploads** — Upload stamp images with automatic resizing/compression via `ffmpeg`
- **AI image analysis** — Optional AI-powered stamp attribute detection (Ollama/llama.cpp compatible)
- **Location management** — Organize stamps by cabinet/shelf/bin via the Settings page
- **Configurable AI** — Adjust AI server URL, model, and prompt from the UI — saved to `config/config.yaml`
- **Responsive UI** — Works on desktop and mobile

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **ffmpeg** and **ffprobe** (for image processing)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Arch Linux: `sudo pacman -S ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Arch Linux Setup

```bash
# Install system packages
sudo pacman -S python nodejs npm base-devel

# Python venv works as described below
# Node.js and npm are provided by the packages above
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp ../config/.env.example ../config/.env  # Optional: for sensitive overrides
```

Edit `config/config.yaml` and set `ai.api_url`, `ai.model`, and optionally `ai.api_key` if you want to use the AI image analysis feature.

Or use the startup script which handles venv creation and dependency installation automatically:

```bash
./start-backend.sh
```

### 2. Frontend

```bash
cd frontend
npm install
```

Or use the startup script:

```bash
./start-frontend.sh
```

### 3. Run the application

**Backend** (port 8000):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (port 3000):
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Config System

The app uses a two-layer configuration:

1. **`config/config.yaml`** — Primary config for database paths, server settings, AI settings, and image limits
2. **`.env`** (in `config/.env`) — Optional env var overrides for sensitive values like API keys

Environment variables take precedence over `config.yaml` values. The frontend Settings page can update AI configuration (server URL, model, prompt) at runtime — changes are persisted to `config/config.yaml`.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite database path (absolute) | `sqlite:///data/product.db` (resolved to project root) |
| `UPLOAD_DIR` | Directory for uploaded images | `data/uploads` |
| `FRONTEND_ORIGIN` | CORS allowed origin | `http://localhost:3000` |
| `AI_API_URL` | Ollama/llama.cpp/llama.cpp server URL | _(from config.yaml)_ |
| `AI_API_KEY` | API key (triggers OpenAI-compatible mode when set) | _(empty)_ |
| `AI_MODEL` | Model name to use | `qwen3.6:35B` |
| `AI_PROMPT` | Custom AI analysis prompt | _(from config.yaml)_ |
| `PROJECT_ROOT` | Override for database/upload path resolution | _(auto-resolved)_ |

## API Endpoints

### Stamps

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stamps` | List all stamps (with optional `q`, `brand_name`, `product_type`, `theme`, `location`, `sentiments` query params) |
| `GET` | `/stamps/{id}` | Get a single stamp by ID |
| `POST` | `/stamps` | Create a new stamp (accepts `multipart/form-data`) |
| `PUT` | `/stamps/{id}` | Update an existing stamp (accepts `multipart/form-data`) |
| `DELETE` | `/stamps/{id}` | Delete a stamp |

### Locations

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/locations` | List all storage locations |
| `POST` | `/locations` | Create a new location (cabinet/shelf/bin) |
| `PUT` | `/locations/{id}` | Update a location |

### AI

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ai/analyze-image` | Analyze a stamp image with AI (accepts optional `ai_api_url` and `ai_prompt` form fields for runtime config override) |

### Configuration

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/config` | Get full application configuration |
| `PUT` | `/api/config/ai` | Update AI configuration (saved to `config/config.yaml`) |

### Static Files

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/uploads/{filename}` | Serve uploaded images |

## Image Upload

- Supported formats: `jpg`, `jpeg`, `png`, `webp`
- Images are automatically resized/compressed to ≤ 1 MB using `ffmpeg`
- Small images are not upscaled
- Files are stored in `data/uploads/` with UUID-based safe filenames

## AI Image Analysis

The AI analysis feature is **optional**. If `AI_API_URL` is not configured, the `/ai/analyze-image` endpoint returns a `501 Not Implemented` response without blocking normal CRUD operations. If a configured AI server fails, the endpoint returns empty suggestions with an error message so regular CRUD usage still works.

To enable AI analysis:

1. Set `ai.api_url` in `config/config.yaml` to your Ollama/llama.cpp server URL (e.g., `http://localhost:11434/v1`)
2. Optionally customize `ai.model` and `ai.prompt`
3. Optionally set `AI_API_KEY` if your server requires authentication

The app auto-detects the API type:
- **OpenAI-compatible** (`/v1/chat/completions`) if the URL contains `/v1` or `AI_API_KEY` is set
- **Ollama** (`/api/chat`) otherwise

You can also configure AI settings directly from the app via **Configuration** in the header. These settings override the `config.yaml` values and are persisted to disk.

The AI endpoint supports runtime configuration overrides — the frontend can pass `ai_api_url` and `ai_prompt` form fields to use different settings per-request without changing the server configuration.

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest test_main.py -v
```

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application, routes, CORS
│   │   ├── database.py      # SQLAlchemy engine and session
│   │   ├── models.py        # SQLAlchemy data model (Stamp, Location)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── crud.py          # Database operations
│   │   ├── image_utils.py   # Image validation and ffmpeg resizing
│   │   └── config.py        # YAML + env var config layer
│   ├── data/
│   │   ├── product.db       # SQLite database
│   │   └── uploads/         # Uploaded images
│   ├── logs/                # Application logs (app.log)
│   ├── uploads/             # Legacy uploads symlink target
│   ├── requirements.txt
│   └── test_main.py         # 20 API tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main app with routing
│   │   ├── main.jsx         # React entry point
│   │   ├── App.css          # Global styles
│   │   ├── pages/
│   │   │   ├── StampsList.jsx    # List/search stamps
│   │   │   ├── StampDetail.jsx   # View stamp details
│   │   │   ├── StampForm.jsx     # Add/edit stamp form
│   │   │   └── Settings.jsx      # Locations + AI config management
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
├── config/
│   └── config.yaml          # Application configuration
├── .env.example
├── start-backend.sh         # Startup script with checks
├── start-frontend.sh        # Startup script with checks
└── README.md
```

## Troubleshooting

- **"ffmpeg not found"** — Ensure ffmpeg and ffprobe are installed and in your PATH
- **CORS errors** — Verify `FRONTEND_ORIGIN` matches your frontend's URL
- **Database locked** — SQLite doesn't support concurrent writes well. Stop all running instances before running migrations
- **Image upload fails** — Check that the `data/uploads/` directory exists and is writable
- **AI analysis not working** — Verify `ai.api_url` in `config/config.yaml` is correct and the server is reachable
