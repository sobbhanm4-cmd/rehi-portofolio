# Vercel setup

1. Import the project root (contains app.py) from Git, or deploy with the Vercel CLI. Use FastAPI defaults, not a static-only deployment. Do not override the output directory to public.
2. Create PostgreSQL through your provider or Vercel Marketplace. Use a PostgreSQL connection string with SSL, not an HTTPS API URL.
3. Run schema.sql once in the database SQL editor. Alternatively export DATABASE_URL locally, install dependencies and run python init_db.py.
4. Configure DATABASE_URL and ADMIN_PASSWORD (24+ random characters) in Vercel Environment Variables. Use a separate preview database if needed.
5. Deploy / redeploy. Log in at /admin.html, open a future date, create a test booking and verify its answers in Bookings. Cancel the test booking afterward.
6. Add your purchased domain in Settings → Domains and follow the exact DNS records shown by Vercel. You can use the vercel.app address before buying a domain.

No database mutation runs during builds. Production refuses SQLite. No automatic Meet generation, external calendar sync, or email delivery is included.

References:
https://vercel.com/docs/frameworks/backend/fastapi
https://vercel.com/docs/marketplace-storage
https://vercel.com/docs/domains/working-with-domains/add-a-domain
