#!/bin/sh
# Self-signed certificate for local/staging only. Browsers will show a warning.
set -e
mkdir -p "$(dirname "$0")/certs"
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout "$(dirname "$0")/certs/privkey.pem" \
  -out "$(dirname "$0")/certs/fullchain.pem" \
  -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
echo "Created deploy/certs/fullchain.pem and privkey.pem"
