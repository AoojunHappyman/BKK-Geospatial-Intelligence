# Vercel + Neon (Free)

Target project: bkkgeo. The bkkgeo.vercel.app alias is subject to availability.
Import the repository root (not frontend) into a Vercel Hobby project.
vercel.json builds React and routes /api/* to the Python ASGI function.

Create a Neon Free PostgreSQL database with PostGIS. Run the existing ETL
locally with DATABASE_URL set to the Neon owner connection string using SSL.
Provision a separate read-only API role using Neon-compatible role management;
the local superuser provisioning script requires review on managed Postgres.
Set DATABASE_URL in Vercel to the read-only role connection string with SSL.
Never use a VITE_ prefix for database credentials.

ETL dependencies and raw data are excluded from Vercel deployment. Run ETL
locally when refreshing data; the deployed API only reads the remote database.
After deployment check /api/health, /api/districts, the dashboard, and direct
navigation to /district/1001. Confirm the requested alias in Vercel Domains.

Deployment and certificate issuance have not been verified until authenticated
Vercel/Neon account access and cloud database initialization are completed.
