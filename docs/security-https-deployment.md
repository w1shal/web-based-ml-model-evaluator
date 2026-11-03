# HTTPS and secure deployment

The application remains usable over plain HTTP for local development. HTTPS enforcement is enabled only when `ENFORCE_HTTPS=1`.

## Local development

Run the backend directly as usual. Keep `ENFORCE_HTTPS=0` and `TRUST_PROXY=0` (the defaults). Set `JWT_SECRET` to a random value of at least 32 bytes before exercising login:

```powershell
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The shared pytest fixtures use a test-only secret; application code has no hard-coded JWT signing fallback.

## Nginx TLS deployment

1. Build the frontend static assets:

   ```sh
   cd frontend
   npm ci
   npm run build
   cd ..
   ```

2. Copy the environment template and generate a fresh signing key. Do not reuse the example or commit the real `.env` file:

   ```sh
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Put the generated value in `JWT_SECRET`. Keep `DATABASE_URL=sqlite:////data/app.db` for the included persistent volume, or configure a production database URL.

3. Provide a trusted certificate and private key at:

   - `deploy/certs/fullchain.pem`
   - `deploy/certs/privkey.pem`

   For local testing only, `sh deploy/gen-dev-cert.sh` creates a self-signed localhost certificate. Browsers will display a certificate warning. Use a certificate issued for your real deployment hostname by a trusted certificate authority in production.

4. Set `ENFORCE_HTTPS=1`, `TRUST_PROXY=1`, and an appropriate comma-separated `CORS_ORIGINS` value in `.env`. Enable `TRUST_PROXY` only when the API is reachable through the configured trusted reverse proxy. The bundled Nginx overwrites the forwarded scheme and client-IP headers.

5. Start the services:

   ```sh
   docker compose -f deploy/docker-compose.yml --env-file .env up --build -d
   ```

Only Nginx publishes host ports 80 and 443. The API listens on port 8000 on the internal Compose network and is not published to the host.

## Security behavior

- Nginx redirects HTTP requests to HTTPS with status 308, preserving the HTTP method.
- Nginx accepts TLS 1.2 and TLS 1.3; older protocol versions are disabled.
- The application middleware also redirects non-HTTPS requests when HTTPS enforcement is enabled.
- `X-Forwarded-Proto` is trusted by application middleware only when `TRUST_PROXY=1`. The rate limiter applies the same explicit opt-in rule to `X-Forwarded-For`.
- The Nginx configuration overwrites `X-Forwarded-For` and `X-Forwarded-Proto` rather than appending client-supplied values.
- The API container runs as a non-root user. Its port is exposed only to the Compose network.
- When `ENFORCE_HTTPS=1`, the application refuses to start if `JWT_SECRET` is missing, uses a known placeholder, or is shorter than 32 bytes.
- Local HTTP development remains available when `ENFORCE_HTTPS` is unset or set to `0`.

Never commit `.env`, generated certificate files, or private keys.
