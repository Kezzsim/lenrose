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

## For further conscideration

- Prefer the client side app talk directly to services (e.g. Tiled, Typesense via instantSearch adapter)
- Minimize functions that the lenrose server is performing, mainly have the web app manage it's own state
- Utilize indexdb e.g. to store state information securely in frontend
