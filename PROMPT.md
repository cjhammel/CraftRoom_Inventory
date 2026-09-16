**Prompt (for a code-generation AI)**

> **Goal** - Build a lightweight web application to inventory craft stamps.
>
> **Required stack**
> - **Backend**: Python FastAPI, SQLAlchemy, Pydantic, SQLite.
> - **Frontend**: React + Vite, plain CSS or a lightweight CSS framework such as Bootstrap, Tailwind, or Bulma.
> - **Database**: SQLite file named `stamps.db` stored in the project root.
> - **Image processing**: Use `ffmpeg` from the backend to resize/compress uploaded images to <= 1 MB while preserving aspect ratio.
>
> **Requirements**
>
> 1. **Data model (SQLite)**
>
>    Create the database table on backend startup using SQLAlchemy `create_all()`. Do not require Alembic migrations unless they are simple and fully wired into the setup instructions.
>
>    ```sql
>    CREATE TABLE stamp (
>        id               INTEGER PRIMARY KEY AUTOINCREMENT,
>        product_name     TEXT    NOT NULL,         -- e.g. "Blue Mauritius"
>        brand_name       TEXT,                      -- brand name
>        product_type     TEXT,                      -- product type
>        image_url        TEXT,                      -- optional URL to an uploaded image
>        theme            TEXT,                      -- stamp set theme
>        shape_descriptor TEXT,                      -- description of the stamp shape
>        sentiments       TEXT,                      -- sentiments seen on the stamp
>        location         TEXT                       -- storage location (box, album, etc.)
>    );
>    ```
>
> 2. **REST API**
>
>    - `GET /stamps` - List all stamps. Support optional query params:
>      - `q`: search by `product_name` or `brand_name`
>      - `brand_name`
>      - `product_type`
>      - `location`
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
>    - **List view**: Table or card grid displaying `product_name`, `brand_name`, `product_type`, `theme`, `shape_descriptor`, `sentiments`, `location`, and a thumbnail when `image_url` exists.
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
>    stamps.db
>    .env.example
>    README.md
>    ```
>
> 7. **Environment configuration**
>
>    Include a `.env.example` file with at least:
>
>    ```env
>    DATABASE_URL=sqlite:///../stamps.db
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
| 1 | Data model (SQLite) | ✅ Complete | `stamp` table with all required columns, `create_all()` on startup |
| 2 | REST API | ✅ Complete | All CRUD endpoints + search/filter working |
| 2a | GET /stamps with filters | ✅ Complete | Supports `q`, `brand_name`, `theme`, `location`, `sentiments` params |
| 2b | GET /stamps/{id} | ✅ Complete | Returns 404 for missing stamps |
| 2c | POST /stamps | ✅ Complete | multipart/form-data, image upload, validation |
| 2d | PUT /stamps/{id} | ✅ Complete | Partial updates, optional image replacement |
| 2e | DELETE /stamps/{id} | ✅ Complete | Removes stamp and associated image file |
| 2f | POST /ai/analyze-image | ✅ Complete | Ollama/llama.cpp compatible endpoint with retry logic |
| 3 | Image upload & resizing | ✅ Complete | ffmpeg resize to <=1MB, no upscaling, safe filenames |
| 4 | AI image analysis | ✅ Complete | Optional, non-blocking, auto-detects API type, 3x retry |
| 5 | Frontend UI | ✅ Complete | React + Vite, responsive, polished |
| 5a | List view (card grid) | ✅ Complete | Thumbnails, metadata display |
| 5b | Search & filters | ✅ Complete | Real-time search, brand/theme/location/sentiments filters, clear button |
| 5c | Detail view | ✅ Complete | Full stamp info, large image, Edit/Delete buttons |
| 5d | Add/Edit form | ✅ Complete | Reusable component, all fields, image preview, rotation controls |
| 5e | Analyze Image button | ✅ Complete | Auto-populates fields from AI response |
| 5f | Client-side validation | ✅ Complete | Required product_name |
| 5g | Delete confirmation modal | ✅ Complete | Modal overlay with cancel/confirm |
| 5h | Image rotation | ✅ Complete | Rotate left/right buttons with canvas-based transformation |
| 6 | Project structure | ✅ Complete | Matches spec with minor adjustments |
| 7 | Environment config | ✅ Complete | `.env.example` with all variables |
| 8 | Setup & run | ✅ Complete | Backend port 8000, frontend port 3000, CORS configured |
| 9 | Tests | ✅ Complete | 18 tests passing (see below) |
| 10a | Drag-and-drop upload | ✅ Complete | Visual feedback, drop zone highlighting |
| 10b | Error logging | ✅ Complete | Comprehensive logging to `backend/logs/app.log` |

### Test Coverage

- ✅ create stamp
- ✅ list stamps
- ✅ retrieve stamp by ID
- ✅ missing stamp returns 404
- ✅ update stamp
- ✅ delete stamp
- ✅ missing stamp delete returns 404
- ✅ search/filter stamps
- ✅ invalid image upload returns 400
- ✅ empty product_name validation
- ✅ AI not configured returns 501
- ✅ image upload and resize (≤ 1MB verification)
- ✅ small image preservation (no upscaling)
- ✅ AI analysis with real image (http://framework.gruru.net:11434)
- ✅ AI analysis with mock response

### Additional Features Added

- **AI integration**: Configured for Ollama/llama.cpp at `http://framework.gruru.net:11434` with `qwen3.6:35B` model, auto-detects API type
- **Comprehensive error logging**: All endpoints log requests, errors with stack traces to `backend/logs/app.log`
- **Drag-and-drop image upload**: Visual feedback with highlight effect when dragging files
- **Arch Linux installation instructions**: Added to README.md
- **Pillow dependency**: Used in tests for creating test images
- **`.gitignore`**: Excludes `.env`, `stamps.db`, `venv/`, `logs/`, uploads
- **Theme filter**: Replaced product_type with theme in search filters (backend + frontend)
- **Clear search button**: Added button to reset all search filters in frontend
- **Multi-word sentiments search**: Splits sentiments query on spaces, matches any term
- **Absolute database path**: `stamps.db` path resolved relative to project root, prevents overwrite on restart

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///stamps.db` (absolute) | SQLite database path (resolved to project root) |
| `UPLOAD_DIR` | `uploads` | Directory for uploaded images |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | CORS allowed origin |
| `AI_API_URL` | `http://framework.gruru.net:11434` | Ollama/llama.cpp server URL (supports `/v1` path) |
| `AI_API_KEY` | _(empty)_ | API key (optional for local servers, triggers OpenAI-compatible mode) |
| `AI_MODEL` | `qwen3.6:35B` | Model name for AI analysis |
| `AI_PROMPT` | _(default prompt)_ | Custom AI analysis prompt with JSON schema |

### AI Endpoint Behavior

- Auto-detects API type: OpenAI-compatible (`/v1/chat/completions`) if URL contains `/v1` or `AI_API_KEY` is set; otherwise uses Ollama (`/api/chat`)
- Strips trailing `/v1` from `AI_API_URL` to prevent duplicate path segments
- Returns 501 with clear message if `AI_API_URL` not configured
- Implements 3x retry logic for empty content responses
- Logs full response and parsing errors to `backend/logs/app.log` for debugging
