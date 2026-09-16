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
>        retired          BOOLEAN NOT NULL DEFAULT 0,-- whether the stamp has been retired
>        product_type     TEXT,                      -- product type
>        image_url        TEXT,                      -- optional URL to an uploaded image
>        theme            TEXT,                      -- stamp set theme
>        shape_descriptor TEXT,                      -- description of the stamp shape
>        sentiments       TEXT,                      -- sentiments seen on the stamp
>        location         TEXT,                      -- storage location (box, album, etc.)
>        price            NUMERIC                    -- purchase price
>    );
>    ```
>
> 2. **REST API**
>
>    - `GET /stamps` - List all stamps. Support optional query params:
>      - `q`: search by `product_name` or `brand_name`
>      - `brand_name`
>      - `product_type`
>      - `price`
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
>    - Validate `price` as a valid decimal value when provided.
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
>    - **List view**: Table or card grid displaying `product_name`, `brand_name`, `product_type`, `retired`, `theme`, `shape_descriptor`, `sentiments`, `location`, `price`, and a thumbnail when `image_url` exists.
>    - Include a search bar and simple filters for `brand_name`, `product_type`, `price`, and `location`.
>    - **Detail view**: Show all fields, a larger image, and `Edit` / `Delete` buttons.
>    - **Add/Edit form**: Re-use the same component. Include fields for every database column except `id` and `image_url`, plus an image file upload input with preview.
>    - Include an `Analyze Image` button that sends the selected image to `POST /ai/analyze-image` and uses the returned JSON to auto-populate matching fields.
>    - Add client-side validation for required `product_name` and valid `price`.
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
