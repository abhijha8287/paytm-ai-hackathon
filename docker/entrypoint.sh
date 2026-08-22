#!/bin/sh
set -e

CERT_DIR=/certs
mkdir -p "$CERT_DIR"

# Self-signed cert regenerated fresh on every container start - cheap, and
# means the phone always trusts the CURRENT LAN IP (which changes per
# network). LAN_IP is passed in from the host at `docker run` time (the
# host knows its own LAN IP; the container, without host networking,
# doesn't). localhost/127.0.0.1 are always included so the laptop itself
# can also use https:// directly.
SAN="DNS:localhost,IP:127.0.0.1"
if [ -n "$LAN_IP" ]; then
  SAN="$SAN,IP:$LAN_IP"
fi

echo "[entrypoint] generating self-signed cert (SAN: $SAN)"
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days 365 \
  -subj "/CN=Paytm Sarthi Demo" \
  -addext "subjectAltName=$SAN"

exec uvicorn main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile "$CERT_DIR/key.pem" \
  --ssl-certfile "$CERT_DIR/cert.pem"
