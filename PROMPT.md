**Prompt (for a code‑generation AI)**

> **Goal** – Build a lightweight web application to inventory craft stamps.
> **Backend** – Use a tiny relational DB (SQLite) for persistence, accessed via a simple REST API. It should also handle image uploads, resizing images with ffmpeg to ≤1 MB while preserving aspect ratio.
> **Frontend** – A minimal single‑page UI (HTML + CSS + JavaScript or a lightweight framework like React/Vite or Svelte) that talks to the API.
>
> **Requirements**
> 1. **Data model (SQLite)**
>    ```sql
>    CREATE TABLE stamp (
>        id           INTEGER PRIMARY KEY AUTOINCREMENT,
>        product_name TEXT    NOT NULL,         -- e.g. “Blue Mauritius”
>        brand_name   TEXT,                     -- Brand Name
>        retired      BOOLEAN,                     -- if the stamp has been retired
>        product_type TEXT,                     -- Product product_type
>        image_url    TEXT,                     -- optional link to an image
>        theme        TEXT,                       -- Stamp set theme
>        shape_descriptor  TEXT,                -- Decribe the shape of the stamp
>        sentiments   TEXT,                     -- Sentiments seen on the stamp
>        location     TEXT,                     -- storage location (box, album, etc.)
>        price    TEXT                          -- Purchise price
>    );
>    ```
> 2. **REST API (e.g. FastAPI/Flask, Express, or similar)**
>    - `GET /stamps` – List all stamps, support optional query params `q` (search by product_name/brand_name), `brand_name`, `product_type`, `price`, `location`.
>    - `GET /stamps/{id}` – Retrieve a single stamp.
>    - `POST /stamps` – Create a new stamp; validate required fields (`product_name`). Accept multipart/form-data for optional image upload; backend must resize the image with ffmpeg to ≤1 MB while preserving aspect ratio, store it in an `uploads/` folder, and set `image_url` accordingly.
>    - `POST /ai/analyze-image` – Accept an image (multipart/form-data), forward it to an AI image‑recognition service; returns inferred stamp attributes (e.g., `product_name`, `brand_name`, `product_type`, etc.) as JSON.
>    - `PUT /stamps/{id}` – Update an existing stamp.
>    - `DELETE /stamps/{id}` – Remove a stamp.
>    - Return JSON with proper HTTP status codes; include CORS headers for the frontend.
> 3. **Frontend UI**
>    - **List view**: Table or card grid displaying `product_name`, `brand_name`, `product_type`, `price`, `location`, and a thumbnail (if `image_url`). Include a search bar and simple filters (brand_name, product_type, price, location).
>    - **Detail view**: Show all fields, larger image, and “Edit” / “Delete” buttons.
>    - **Add/Edit form**: Re‑use the same component; fields for all columns; include an image file upload input with preview and an 'Analyze Image' button that sends the image to the AI endpoint to auto‑populate fields; client‑side validation for required `product_name`.
>    - **Delete confirmation** modal.
>    - Use a CSS framework (Bootstrap, Tailwind, or Bulma) for quick, responsive styling.
>    - Communicate with the API via `fetch`/`axios`.
> 4. **Project structure** (example for a Python‑FastAPI backend + React frontend)
>    ```
>    /backend
>        ├─ app/
>        │   ├─ main.py
>        │   ├─ models.py   (SQLAlchemy models)
>        │   ├─ schemas.py  (Pydantic)
>        │   └─ crud.py
>        └─ requirements.txt
>    /frontend
>        ├─ src/
>        │   ├─ components/
>        │   ├─ pages/
>        │   └─ App.jsx
>        └─ package.json
>    ```
>    Adjust for a Node/Express backend if preferred; keep the same DB file (`stamps.db`) in the project root.
> 5. **Setup & run**
>    - Backend: `python -m venv venv && pip install -r requirements.txt && uvicorn app.main:app --reload` (or `npm start` for Express).
>    - Frontend: `npm install && npm run dev` (Vite) or `npm start` (Create‑React‑App).
>    - Both services should listen on different ports (e.g., backend 8000, frontend 3000) and work together via CORS.
> 6. **Optional extras** (add if time permits)
>    - Basic authentication (username/password) protecting all API routes.
>    - CSV import/export of the stamp collection.
>    - Drag‑and‑drop image upload; backend resizes images using ffmpeg and stores them in `uploads/`, setting `image_url` accordingly.
>    - Simple unit tests for the API endpoints (pytest or Jest).
>
>**Deliverables**
>- Fully functional backend code with SQLite DB migrations.
>- Minimal but polished frontend UI meeting the above spec.
>- `README.md` with install/run instructions.
>
>*Use this prompt to ask an AI code‑generator (e.g., Copilot, GPT‑4, or a scaffolding tool) to produce the complete application.*
