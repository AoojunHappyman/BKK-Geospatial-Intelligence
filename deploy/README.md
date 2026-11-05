# Public HTTPS deployment

Use a Linux VPS with Docker Compose and persistent disk for PostgreSQL and
Caddy certificates. Start with 2 vCPU / 4 GB RAM as an initial sizing estimate;
measure memory and query latency before increasing traffic.

1. Obtain a VPS and a domain in your own account. Use `geo.your-domain` as the
   site hostname. Set its DNS A record to the VPS public IPv4 address. Set AAAA
   only if IPv6 routing to the VPS is configured.
2. Allow inbound TCP 80/443 (and optionally UDP 443 for HTTP/3). Keep database
   and API ports private. Enable Docker startup on boot.
3. Copy `.env.example` to `.env`, set distinct random URL-safe database passwords,
   and set `SITE_DOMAIN` to the hostname only, without scheme, path or port.
4. From the repository root:

```sh
docker compose -f docker-compose.yml -f docker-compose.https.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.https.yml up --build -d
docker compose -f docker-compose.yml -f docker-compose.https.yml logs proxy
```

Caddy obtains and renews the certificate and redirects HTTP to HTTPS. The
browser uses the same hostname for the UI and `/api/`; no frontend API URL
change is needed. The original port 8080 stays bound to host loopback only.
Keep `caddy_data` and `postgres_data`; do not remove these volumes on upgrades.
Use both Compose files for subsequent starts, updates and stops.

After startup, check `https://YOUR_HOST/api/health`, load the dashboard and
confirm that `http://YOUR_HOST` redirects to HTTPS with a trusted certificate.
Certificate issuance requires correct public DNS and reachable ports. Until
that check passes, public deployment is not complete.

This configuration does not provision a VPS, purchase a domain or configure DNS.
Reference: https://caddyserver.com/docs/automatic-https
