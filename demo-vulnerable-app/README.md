# Demo Vulnerable App

This app is intentionally vulnerable for security demos.

## Features
- Small realistic UI in `public/`
- Vulnerable endpoints:
  - `POST /api/login`
  - `GET /api/search?q=...`
   - `GET /api/users?sort=...`
   - `GET /api/orders?user=...`
  - `POST /api/comment`
  - `GET /api/file?path=...`
   - `POST /api/admin/run`
   - `GET /api/export?format=...`
   - `POST /api/xml/import`
   - Discovery paths: `/admin`, `/.env`, `/backup.zip`, `/phpmyadmin`, `/wp-admin`
- Optional MicroShield middleware integration

## Quick Start
1. Copy `.env.example` to `.env`
2. Install packages:
   - `npm install`
3. Run app:
   - `npm start`
4. Open browser:
   - `http://127.0.0.1:4100`

## MicroShield Integration
Set:
- `ENABLE_MICROSHIELD=1`
- `MICROSHIELD_MODULE_PATH` to your local middleware module path

Example path on your machine:
- `C:/Users/mayan/microshield-npm/index.js`

The app automatically sends tenant/user headers from env values so logs are separated.

## Telemetry DB Location
When MicroShield is enabled, events are stored at:
- `demo-vulnerable-app/data/microshield_events.sqlite`

You can also confirm this path from:
- `GET /api/status` (`telemetryDbPath` field)

## Manual Testing Flow

1. Open the UI and use built-in forms + manual request console.
2. Try payloads manually (SQLi/XSS/traversal/command style) against app routes.
3. Keep MicroShield ON to see what gets blocked vs allowed.
4. Review events in your dashboard or observability APIs.

## Bot Tool Testing (Localhost Only)

If you use tools like sqlmap, hydra, or gobuster, run them only against your local demo target:
- `http://127.0.0.1:4100`

Never target systems you do not own or have explicit authorization to test.
