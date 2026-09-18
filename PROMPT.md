**Prompt (for a code-generation AI)**

> **Goal** - Build a lightweight web application to inventory craft stamps.
>
> **Required stack**
> - **Backend**: Python FastAPI, SQLAlchemy, Pydantic, SQLite.
> - **Frontend**: React + Vite, plain CSS or a lightweight CSS framework such as Bootstrap, Tailwind, or Bulma.
> - **Database**: SQLite file named `product.db` stored in the project root.
> - **Image processing**: Use `ffmpeg` from the backend to resize/compress uploaded images to <= 1 MB while preserving aspect ratio.
>
> **Requirements**
>
> 1. **Data model (SQLite)**
>
>    Create the database table on backend startup using SQLAlchemy `create_all()`. Do not require Alembic migrations unless they are simple and fully wired into the setup instructions.
>
>    ```sql
>    CREATE TABLE location (
>        id               INTEGER PRIMARY KEY AUTOINCREMENT,
>        cabinet          TEXT,                      -- cabinet name/number
>        shelf            TEXT,                      -- shelf name/number
>        bin              TEXT                       -- bin name/number
>    );
>
>    CREATE TABLE product (
>        id               INTEGER PRIMARY KEY AUTOINCREMENT,
>        product_name     TEXT    NOT NULL,         -- e.g. "Blue Mauritius"
>        brand_name       TEXT,                      -- brand name
>        product_type     TEXT,                      -- product type
>        image_url        TEXT,                      -- optional URL to an uploaded image
>        theme            TEXT,                      -- stamp set theme
>        shape_descriptor TEXT,                      -- description of the stamp shape
>        sentiments       TEXT,                      -- sentiments seen on the stamp
>        location_id      INTEGER,                   -- storage location reference
>        FOREIGN KEY (location_id) REFERENCES location(id)
>    );
>    ```
>
> 2. **REST API**
>
>    - `GET /stamps` - List all stamps. Support optional query params:
>      - `q`: search by `product_name` or `brand_name`
>      - `brand_name`
>      - `product_type`
>      - `location`: search by linked location `cabinet`, `shelf`, or `bin`
>    - `GET /stamps/{id}` - Retrieve a single stamp. Return `404` when the stamp does not exist.
>    - `POST /stamps` - Create a new stamp. Accept `multipart/form-data` so the request can include fields plus an optional image file. Validate that `product_name` is present and non-empty.
>    - `PUT /stamps/{id}` - Update an existing stamp. Accept `multipart/form-data`. Image replacement is optional; keep the existing image when no new image is uploaded. Return `404` when the stamp does not exist.
>    - `DELETE /stamps/{id}` - Remove a stamp. Return `404` when the stamp does not exist.
>    - `POST /ai/analyze-image` - Accept an image as `multipart/form-data` and return inferred stamp attributes as JSON, such as `product_name`, `brand_name`, `product_type`, `theme`, `shape_descriptor`, and `sentiments`.
>
>    API behavior:
>    - Return JSON responses with proper HTTP status codes.
>    - Include CORS headers so the React frontend can call the backend from `http://localhost:3000` or the configured frontend origin.
>    - Validate uploaded file types. Support at least `jpg`, `jpeg`, `png`, and `webp`.
>    - Reject unsupported image types or invalid payloads with `400`.
>    - Serve uploaded images from `/uploads/{filename}`.
>
> 3. **Image upload and resizing**
>
>    - Store uploaded images in a backend `uploads/` folder.
>    - Use safe generated filenames to avoid collisions and path traversal.
>    - Use `ffmpeg` to resize/compress images to <= 1 MB while preserving aspect ratio.
>    - Do not upscale small images.
>    - Set `image_url` to the public URL returned by the backend, for example `/uploads/example.webp`.
>    - The frontend must show thumbnails in the list view and a larger image in the detail view.
>
> 4. **AI image analysis behavior**
>
>    - Make the AI integration optional and non-blocking for the rest of the app.
>    - Read the AI credential from `AI_API_KEY`.
>    - If `AI_API_KEY` is not configured, `POST /ai/analyze-image` should return either `501 Not Implemented` with a clear JSON message or a safe mocked response with empty suggestions.
>    - Do not hard-code secrets.
>    - Document where to configure the AI provider in the README.
>
> 5. **Frontend UI**
>
>    - **List view**: Table or card grid displaying `product_name`, `brand_name`, `product_type`, `theme`, `shape_descriptor`, `sentiments`, linked location, and a thumbnail when `image_url` exists.
>    - Include a search bar and simple filters for `brand_name`, `product_type`, and `location`.
>    - **Detail view**: Show all fields, a larger image, and `Edit` / `Delete` buttons.
>    - **Add/Edit form**: Re-use the same component. Include fields for every database column except `id` and `image_url`, plus an image file upload input with preview.
>    - Include an `Analyze Image` button that sends the selected image to `POST /ai/analyze-image` and uses the returned JSON to auto-populate matching fields.
>    - Add client-side validation for required `product_name`.
>    - Include a delete confirmation modal.
>    - Use `fetch` or `axios` to communicate with the API.
>    - The UI should be minimal, polished, responsive, and usable on desktop and mobile.
>
> 6. **Project structure**
>
>    Use this structure unless a small adjustment is necessary:
>
>    ```text
>    /backend
>        /app
>            main.py
>            database.py
>            models.py
>            schemas.py
>            crud.py
>            image_utils.py
>        /uploads
>        requirements.txt
>    /frontend
>        /src
>            /components
>            /pages
>            App.jsx
>            main.jsx
>        package.json
>    product.db
>    .env.example
>    README.md
>    ```
>
> 7. **Environment configuration**
>
>    Include a `.env.example` file with at least:
>
>    ```env
>    DATABASE_URL=sqlite:///../product.db
>    UPLOAD_DIR=uploads
>    FRONTEND_ORIGIN=http://localhost:3000
>    AI_API_KEY=
>    AI_PROMPT=
>    ```
>
> 8. **Setup and run**
>
>    Backend:
>
>    ```bash
>    cd backend
>    python -m venv venv
>    source venv/bin/activate
>    pip install -r requirements.txt
>    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
>    ```
>
>    Frontend:
>
>    ```bash
>    cd frontend
>    npm install
>    npm run dev -- --host 0.0.0.0 --port 3000
>    ```
>
>    The backend should listen on port `8000`, the frontend should listen on port `3000`, and they should work together through CORS.
>
> 9. **Required tests**
>
>    Add minimal API tests using `pytest` and FastAPI's test client. Cover:
>    - create stamp
>    - list stamps
>    - search/filter stamps
>    - retrieve stamp by ID
>    - update stamp
>    - delete stamp
>    - missing stamp returns `404`
>    - invalid image upload returns `400`
>
> 10. **Optional extras**
>
>    Add only if the core app is complete first:
>    - Basic authentication with username/password protecting all API routes.
>    - CSV/json import/export of the stamp collection.
>    - Drag-and-drop image upload in the frontend.
>    - Thumbnail generation in addition to the resized full image.
>
> **Deliverables**
>
> - Fully functional FastAPI backend with SQLite persistence.
> - React/Vite frontend meeting the UI requirements.
> - Working image upload, ffmpeg resizing, static serving, and image previews.
> - Optional/mockable AI image-analysis endpoint that does not block normal CRUD usage.
> - Minimal API tests.
> - `.env.example`.
> - `README.md` with install, run, test, and troubleshooting instructions.
>
> **Acceptance criteria**
>
> - A new user can follow the README from a fresh clone and run the backend and frontend successfully.
> - The user can create, view, edit, delete, search, and filter stamps.
> - Uploaded images are resized to <= 1 MB, stored in `uploads/`, served by the backend, and visible in the frontend.
> - The app works even when `AI_API_KEY` is not configured.
> - API tests pass with `pytest`.
>
> Use this prompt to generate the complete application. Prefer simple, readable code over unnecessary abstractions.

---

## Implementation Status

### Completed Features

| # | Requirement | Status | Notes |
|---|---|---|---|
| 1 | Data model (SQLite) | ✅ Complete | `product` table + `location` table, `create_all()` on startup |
| 1a | `item_number` field | ✅ Added | Extra field not in original spec |
| 2 | REST API | ✅ Complete | All CRUD + search/filter + location management |
| 2a | GET /stamps with filters | ✅ Complete | `q`, `brand_name`, `product_type`, `theme`, `location`, `sentiments` |
| 2b | GET /stamps/{id} | ✅ Complete | Returns 404 for missing stamps |
| 2c | POST /stamps | ✅ Complete | multipart/form-data, image upload, validation |
| 2d | PUT /stamps/{id} | ✅ Complete | Partial updates, optional image replacement |
| 2e | DELETE /stamps/{id} | ✅ Complete | Removes stamp and associated image file |
| 2f | POST /ai/analyze-image | ✅ Complete | Ollama/llama.cpp compatible, runtime config override |
| 2g | Location CRUD | ✅ Added | GET/POST/PUT /locations for managing storage locations |
| 2h | AI config endpoints | ✅ Added | GET /api/config, PUT /api/config/ai — save to config.yaml |
| 3 | Image upload & resizing | ✅ Complete | ffmpeg resize to ≤1MB, no upscaling, UUID safe filenames |
| 4 | AI image analysis | ✅ Complete | Optional, non-blocking, auto-detects API type, 3x retry, markdown JSON extraction |
| 5 | Frontend UI | ✅ Complete | React + Vite, responsive, polished |
| 5a | List view (card grid) | ✅ Complete | Thumbnails, metadata display |
| 5b | Search & filters | ✅ Complete | Search bar, brand/product type/theme/location/sentiments filters, clear button |
| 5c | Detail view | ✅ Complete | Full stamp info, large image, Edit/Delete buttons |
| 5d | Add/Edit form | ✅ Complete | Reusable component, all fields, image preview, rotation controls |
| 5e | Analyze Image button | ✅ Complete | Auto-populates fields from AI response |
| 5f | Client-side validation | ✅ Complete | Required product_name |
| 5g | Delete confirmation modal | ✅ Complete | Modal overlay with cancel/confirm |
| 5h | Image rotation | ✅ Complete | Canvas-based left/right rotation |
| 5i | Settings page | ✅ Added | Tabs for Locations management and AI server configuration |
| 6 | Project structure | ✅ Complete | Uses `config/config.yaml`, `data/` subdirectory for DB/uploads |
| 7 | Environment config | ✅ Complete | `.env.example` + YAML config with env var override |
| 8 | Setup & run | ✅ Complete | Backend port 8000, frontend port 3000, CORS configured, startup scripts |
| 9 | Tests | ✅ Complete | 20 tests passing (see below) |
| 10a | Drag-and-drop upload | ✅ Complete | Visual feedback, drop zone highlighting |
| 10b | Error logging | ✅ Complete | All endpoints log to `backend/logs/app.log` with stack traces |

### Test Coverage (20 tests)

- ✅ test_create_stamp
- ✅ test_list_stamps
- ✅ test_create_and_update_location
- ✅ test_create_stamp_with_location_id
- ✅ test_get_stamp_by_id
- ✅ test_get_stamp_404
- ✅ test_update_stamp
- ✅ test_delete_stamp
- ✅ test_delete_stamp_404
- ✅ test_search_stamps
- ✅ test_invalid_image_upload
- ✅ test_create_stamp_empty_product_name
- ✅ test_update_stamp_404
- ✅ test_update_stamp_empty_product_name
- ✅ test_ai_analyze_not_configured
- ✅ test_image_upload_and_resize
- ✅ test_image_upload_preserves_small_images
- ✅ test_ai_analyze_with_real_image
- ✅ test_ai_analyze_with_mock_response
- ✅ test_ai_analyze_uses_request_configuration

### Additional Features Added

- **AI integration**: Ollama + OpenAI-compatible auto-detection, markdown JSON extraction, 3x retry with backoff, runtime config override via form params, config saved to `config/config.yaml`
- **Config endpoints**: `GET /api/config` (read full config), `PUT /api/config/ai` (update AI settings) — accessible from frontend Settings page
- **Comprehensive error logging**: All endpoints log requests, errors with stack traces to `backend/logs/app.log`
- **Drag-and-drop image upload**: Visual feedback with highlight effect when dragging files
- **Location management**: Full CRUD for storage locations (cabinet/shelf/bin) via Settings page
- **Startup scripts**: `start-backend.sh` and `start-frontend.sh` with colored output, version checks, auto-venv setup
- **YAML-based config**: `config/config.yaml` with env var override via `app.config` module
- **`.gitignore`**: Excludes `.env`, `config/.env`, `*.db`, `venv/`, `logs/`, `node_modules/`, `frontend/dist/`
- **Clear search button**: Reset all search filters in frontend
- **AI settings persistence**: AI server URL, model, and prompt saved to `config/config.yaml` and editable from the UI

### Config System

The app uses a two-layer config system:
1. **`config/config.yaml`** — Primary config file (database, paths, server, AI, image settings)
2. **`.env` / environment variables** — Override values from config.yaml (sensitive values like API keys)

The config module (`app/config.py`) checks env vars first, then falls back to `config.yaml` values.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/product.db` (resolved to project root) | SQLite database path |
| `UPLOAD_DIR` | `data/uploads` (resolved to project root) | Directory for uploaded images |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowed origin |
| `AI_API_URL` | _(from config.yaml)_ | Ollama/llama.cpp/llama.cpp server URL |
| `AI_API_KEY` | _(empty)_ | API key (triggers OpenAI-compatible mode when set) |
| `AI_MODEL` | `qwen3.6:35B` | Model name for AI analysis |
| `AI_PROMPT` | _(from config.yaml)_ | Custom AI analysis prompt with JSON schema |
| `PROJECT_ROOT` | _(auto-resolved)_ | Override for database/upload path resolution |

### AI Endpoint Behavior

- **API type auto-detection**: OpenAI-compatible (`/v1/chat/completions`) if URL contains `/v1` or `AI_API_KEY` is set; otherwise Ollama (`/api/chat`)
- **Path normalization**: Strips trailing `/v1` from `AI_API_URL` to prevent duplicate path segments
- **Runtime config override**: Frontend can pass `ai_api_url` and `ai_prompt` form fields to override server defaults per-request
- **501 response**: Clear JSON message if `AI_API_URL` not configured in either env or config.yaml
- **3x retry**: Retries on empty content responses and HTTP errors with 1-second backoff
- **Markdown JSON extraction**: Parses ```json code blocks from LLM responses
- **Logging**: Full request/response logging to `backend/logs/app.log` for debugging
