#!/bin/sh
# Builds and runs Paytm Sarthi in Docker, detects this machine's LAN IP,
# and prints the URL to open on a phone on the same wifi.
set -e

if [ "$(uname)" = "Darwin" ]; then
  LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
else
  LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

if [ -z "$LAN_IP" ]; then
  echo "Couldn't auto-detect a LAN IP. Find yours manually (e.g. 'ifconfig' /"
  echo "'ipconfig') and run: LAN_IP=<your-ip> docker compose up --build"
  exit 1
fi

if [ ! -f .env ]; then
  echo "No .env file found. Copy .env.example to .env and set SARVAM_API_KEY first."
  exit 1
fi

export LAN_IP
echo "Building and starting Paytm Sarthi..."
echo "LAN IP detected: $LAN_IP"
echo ""
echo "  On this laptop:  https://localhost:8000"
echo "  On your phone:   https://$LAN_IP:8000   (same wifi network)"
echo ""
echo "Your phone's browser will warn about the self-signed certificate -"
echo "this is expected (see README.md). Tap through it once."
echo ""

docker compose up --build
