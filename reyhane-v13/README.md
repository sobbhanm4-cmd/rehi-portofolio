# RN Studio — custom FastAPI booking

Read **GUIDE-FA.md** for the complete Persian setup and media guide.

- `public/`: original sky-blue portfolio, calendar, qualification form, admin dashboard and click-to-load YouTube embeds.
- `app.py`: FastAPI endpoints; `db.py`: SQLAlchemy models.
- `schema.sql` / `init_db.py`: explicit initial database setup.
- PostgreSQL required on Vercel. SQLite supported only locally.
- Admin password stays in browser memory; API responses use no-store. Server validation, persistent rate limiting and database uniqueness protect bookings.
- All budget tiers accepted. New requests reserve the slot immediately. Cancellation releases it.
- Meet links are entered/shared manually. No automatic email, calendar synchronization or migration of old Google Calendar bookings.

## Local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Set ADMIN_PASSWORD to a random value of at least 24 characters in your shell.
python init_db.py
uvicorn app:app --reload
```
Environment files are not auto-loaded. See .env.example. Never commit secrets or local databases.

## Vercel
Import the repository root as FastAPI; do not set Output Directory to public. Configure DATABASE_URL and ADMIN_PASSWORD. Run schema.sql in your PostgreSQL SQL editor before using bookings, then deploy. public/ is served by Vercel; FastAPI mounts it only locally. Run a real booking test after deploying.

## Tests
```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Media
Edit public/content.js. Accepts YouTube watch, youtu.be, embed, Shorts and live URLs. Thumbnail only before click; no video files are bundled. See GUIDE-FA.md for the nine video slots.

## Operations
Use HTTPS. Rotate ADMIN_PASSWORD in Vercel and redeploy if needed. Rate limits use persistent atomic counters and Vercel's trusted x-vercel-forwarded-for header. No CAPTCHA, password recovery, automatic data-retention schedule or automatic client notifications are configured. Manage data retention in the database according to business requirements. Old calendar reservations must be migrated or their slots manually closed if replacing a previously live site.
