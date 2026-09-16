# CraftRoom Stamp Inventory

A lightweight web application to inventory craft stamps. Built with FastAPI (backend) and React + Vite (frontend).

## Features

- **CRUD operations** — Create, view, edit, and delete stamps
- **Search & filter** — Search by name/brand, filter by type, brand, location
- **Image uploads** — Upload stamp images with automatic resizing/compression via `ffmpeg`
- **AI image analysis** — Optional AI-powered stamp attribute detection (requires API key)
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
cp ../.env.example .env
```

Edit `.env` and set your `AI_API_KEY` if you want to use the AI image analysis feature.

### 2. Frontend

```bash
cd frontend
npm install
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

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite database path | `sqlite:///../stamps.db` |
| `UPLOAD_DIR` | Directory for uploaded images | `uploads` |
| `FRONTEND_ORIGIN` | CORS allowed origin | `http://localhost:3000` |
| `AI_API_URL` | llama.cpp / Ollama server URL | `http://example.com:11434` |
| `AI_API_KEY` | API key (optional for some providers) | _(empty)_ |
| `AI_MODEL` | Model name to use | `qwen3.6:35B` |
| `AI_PROMPT` | Custom AI analysis prompt | _(default prompt)_ |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stamps` | List all stamps (with optional `q`, `brand_name`, `product_type`, `location` query params) |
| `GET` | `/stamps/{id}` | Get a single stamp by ID |
| `POST` | `/stamps` | Create a new stamp (accepts `multipart/form-data`) |
| `PUT` | `/stamps/{id}` | Update an existing stamp (accepts `multipart/form-data`) |
| `DELETE` | `/stamps/{id}` | Delete a stamp |
| `POST` | `/ai/analyze-image` | Analyze a stamp image with AI (returns inferred attributes) |
| `GET` | `/uploads/{filename}` | Serve uploaded images |

## Image Upload

- Supported formats: `jpg`, `jpeg`, `png`, `webp`
- Images are automatically resized/compressed to <= 1 MB using `ffmpeg`
- Small images are not upscaled
- Files are stored in the `backend/uploads/` directory with safe, UUID-based filenames

## AI Image Analysis

The AI analysis feature is **optional**. If the AI server (`AI_API_URL`) is not reachable, the `/ai/analyze-image` endpoint returns a `501 Not Implemented` response without blocking normal CRUD operations.

To enable AI analysis:

1. Ensure the llama.cpp / Ollama-compatible server is running at `AI_API_URL` (default: `http://example.com:11434`)
2. The server should have the model `qwen3.6:35B` available (or set `AI_MODEL` in `.env`)
3. Optionally customize `AI_PROMPT` to change the analysis behavior
4. Set `AI_API_KEY` if your server requires authentication

The app uses the Ollama-compatible `/api/chat` endpoint with multimodal (image) support.

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
│   │   ├── models.py        # SQLAlchemy data model
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── crud.py          # Database operations
│   │   └── image_utils.py   # Image validation and ffmpeg resizing
│   ├── uploads/             # Uploaded images
│   ├── requirements.txt
│   └── test_main.py         # API tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main app with routing
│   │   ├── main.jsx         # React entry point
│   │   ├── App.css          # Global styles
│   │   ├── pages/
│   │   │   ├── StampsList.jsx    # List/search stamps
│   │   │   ├── StampDetail.jsx   # View stamp details
│   │   │   └── StampForm.jsx     # Add/edit stamp form
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

## Troubleshooting

- **"ffmpeg not found"** — Ensure ffmpeg and ffprobe are installed and in your PATH
- **CORS errors** — Verify `FRONTEND_ORIGIN` matches your frontend's URL
- **Database locked** — SQLite doesn't support concurrent writes well. Stop all running instances before running migrations
- **Image upload fails** — Check that the `backend/uploads/` directory exists and is writable
