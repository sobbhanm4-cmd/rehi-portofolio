# Validation — custom FastAPI booking

Executed locally on 2026-09-22:
- 5 pytest cases passed: complete booking lifecycle/idempotency/cancellation; concurrent same-slot booking (one 201, one 409); invalid fields/date/time/consent and private API/static-file isolation; persistent login throttle; public submission throttle.
- Chromium desktop (1440px) and mobile (390px): selected a real available time, filled qualification fields, submitted a booking through FastAPI, logged into the admin UI, verified answers and cancelled the booking.
- Mobile page and dashboard had no horizontal overflow; screenshots visually inspected.
- No uncaught JavaScript errors in the browser flow.
- YouTube watch, short-link and Shorts URL normalization checked, unrelated host rejected; iframe created only on click. The player network response was mocked, so actual playback requires the owner's embeddable YouTube links.
- JavaScript syntax checked with node --check.

Limits: database tests used local SQLite. PostgreSQL constraints/DDL are included, but no live external PostgreSQL account or Vercel account was available for production integration tests. Domain DNS, actual YouTube playback, production database connectivity and deployment must be checked after setup. External calendar sync, automatic email and automatic Google Meet creation are not implemented.

Timezone update: all booking, calendar and dashboard timezone references now use Asia/Dubai (UTC+04:00). The 5 backend tests passed again, including assertions for the public timezone and saved booking timestamp offset. JavaScript syntax checks passed. Earlier screenshots are omitted because they predate the timezone update.
