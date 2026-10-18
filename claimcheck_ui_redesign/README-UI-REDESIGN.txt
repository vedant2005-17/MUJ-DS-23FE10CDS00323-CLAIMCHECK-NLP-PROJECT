# Claimcheck UI redesign

This package contains a frontend-only redesign for your existing Flask Claimcheck project.

## Files to replace
- Replace `templates/index.html` with this package's `templates/index.html`
- Replace `static/app.js` with this package's `static/app.js`
- Replace `static/style.css` with this package's `static/style.css`

Keep your existing `app.py`, `config.yaml`, `detector/`, `prompts/`, `.env`, and requirements unchanged.
The frontend continues to call the existing `POST /api/analyze` endpoint.

## Notes
- The History link explains that analysis history is not persisted; it does not pretend to save history.
- Scores and verdicts come from the backend response, not hardcoded demo data.
- Google Fonts require internet access; fallback fonts are included.
- Do not share your `.env` file. If its API key was exposed, revoke it and create a replacement.
