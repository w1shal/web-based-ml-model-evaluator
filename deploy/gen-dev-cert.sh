#!/bin/sh
# Local development/staging only. Browsers will warn because this is self-signed.
# Replace these certificates with a trusted CA-issued certificate in production.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CERT_DIR="$SCRIPT_DIR/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:3072 -days 30 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERT_DIR/privkey.pem"
printf '%s\n' "Created local self-signed certificates in deploy/certs/."
