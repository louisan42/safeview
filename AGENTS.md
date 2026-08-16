## Learned User Preferences
- Prefer a light-only civic UI; do not add dark mode.
- Avoid generic AI-slop aesthetics (Inter/system stacks, purple neon, dark ops dashboards, muted gold or forest-green palettes).
- Use fun, clean, simple fonts (Nunito is the current family); skip editorial serif display pairings.
- Keep UI chrome (buttons, selected chips, focus rings) solid blue so it does not clash with crime-density red on the map.
- Choropleth and incident colors should be solid yellow → orange → red; red means red and yellow means yellow.
- Draw real neighbourhood boundary polygons on the map, not rectangles or bounding boxes.
- Address search should autocomplete with selectable suggestions so geocoding does not drift.
- Overlay panels (autocomplete, dropdowns) must stack above other chrome.
- Header eyebrow is NEIGHBOURHOOD (not TORONTO); the wordmark below stays Watchtile.
- Details chart: window overlay (current vs previous) as default; hood-vs-hood overlay in compare; By category small multiples as opt-in.

## Learned Workspace Facts
- Product display name is Watchtile (full lockup: Neighbourhood Watchtile; former UI name Lotline); the workspace folder and GitHub repo remain SafetyView / louisan42/safeview.
- Stack is FastAPI (`api/`), React + Leaflet (`web/`), PostGIS, and ETL from Toronto Police Service open data (robbery, theft over, break and enter).
- Railway hosts API, web, and production Postgres+PostGIS. GitHub Source on `louisan42/safeview` deploys production from `main` after CI (Wait for CI). Staging is the PR-environment base with its own PostGIS. Coolify and `railway up` are not the happy path.
- Weekly ETL runs on GitHub Actions against Railway Postgres.
- Local defaults: API on port 8888, Vite often on 5173 (3000 is frequently occupied), Docker PostGIS `sv_db_dev` on 55432.
- Brand assets live in `web/public/` (`logo.svg`, `favicon.svg`, `logo-lockup.svg`): house-roof tessellation; UI accent is blue `#2563EB`.
- The map uses the real 158 Toronto neighbourhood polygons.
- `etl/config.yaml` can contain live database credentials — never commit it, and never print or log DSNs (the GitHub repo is public).
- Railway MCP is available for this project.
- Staging/PR web auth uses Clerk development (`@clerk/react`, `VITE_CLERK_PUBLISHABLE_KEY`). Production stays public until a `pk_live_` key is set on the production web service.
