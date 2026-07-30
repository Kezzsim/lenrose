# Lenrose development guidelines

## Ideal languages and toolings

- Backend should consist of a fastapi python server
- utilizing libraries like starlette e.g. to manage http
- frontend should exclusively be react written in typescript
- Vite.js for frontend design
- Visually follow the MUI graphical design standards
- Incorporate Brookhaven National Laboratory branding guidelines for NSLS-II
- typesense native client APIs for the python backend and frontend
- Bluesky Tiled is the core library that this program interfaces with
- Pixi instead of uv or conda for end to end supply chain management

## Testing methodologies

- Composible pytest
- fixtures for setting up a typesense connection
- Github Actions that set up a typesense container and route requests there
- pytest-vcr to play back canned http responses
