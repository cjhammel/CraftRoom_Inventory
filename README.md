# CraftRoom Inventory

CraftRoom Inventory is a planned lightweight web application for cataloging and managing a craft stamp collection.

The goal is to make it easy to record each stamp's product details, storage location, purchase price, image, and descriptive metadata so the collection can be searched, filtered, and maintained from a simple browser interface.

## Project Goals

- Provide a simple inventory system for craft stamps.
- Store stamp records in a local SQLite database.
- Offer a REST API for creating, viewing, updating, deleting, searching, and filtering stamps.
- Include a responsive single-page frontend for managing the collection.
- Support image uploads for stamps, including backend resizing/compression with `ffmpeg`.
- Optionally analyze uploaded images with an AI service to suggest stamp attributes.
- Keep the application easy to run locally from a fresh clone.

## Target Stack

- Backend: Python, FastAPI, SQLAlchemy, Pydantic, SQLite
- Frontend: React + Vite
- Image processing: `ffmpeg`
- Tests: `pytest` with FastAPI's test client

## Planned Features

- Stamp list view with thumbnails, search, and filters.
- Stamp detail view with all recorded fields and a larger image.
- Add/edit form with validation and image preview.
- Delete confirmation flow.
- Uploaded images stored locally and served by the backend.
- Optional AI-powered image analysis endpoint that can safely fall back when no API key is configured.

## Planned Stamp Data

Each stamp record should include:

- Product name
- Brand name
- Retired status
- Product type
- Image URL
- Theme
- Shape descriptor
- Sentiments
- Storage location
- Purchase price

## Development Prompt

The detailed implementation prompt is maintained in [`PROMPT.md`](PROMPT.md). It defines the expected API routes, database schema, frontend behavior, setup commands, tests, deliverables, and acceptance criteria for generating the full application.

## License

This project is licensed under the MIT License. See [`LICENSE.md`](LICENSE.md).
