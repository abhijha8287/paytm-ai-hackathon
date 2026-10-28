# Paytm Sarthi: Cross-Language Voice Payment

A merchant says a payment amount aloud in any language; the payer sees and hears it in their own language, confirms, and completes a simulated payment.

## Why this exists
Built for a Paytm AI hackathon. In India, a shopkeeper and a customer often do not share a language, which makes it easy to misunderstand the amount at the counter.

## What it does
- Identifies the payer by scanning a QR code or typing a UPI ID (demo only, nothing is verified)
- Records the merchant speaking an amount; the language is detected automatically
- Translates and extracts the amount with Sarvam AI (Saaras v3 speech-to-English, Sarvam-M fallback)
- Speaks the confirmation back in the payer's chosen language with Bulbul text-to-speech
- Creates a local payment reference and a scannable UPI-style QR code
- Simulates success or decline; no Paytm or other payment provider is called
- Falls back to manual amount entry if the mic is blocked or the amount is unclear

## Project structure
```
paytm-ai-hackathon/
├── main.py             FastAPI app and Sarvam calls
├── static/             Web page, QR scanner and generator
├── docker/             Container entrypoint (HTTPS cert)
├── Dockerfile          Container image
├── docker-compose.yml  Local HTTPS setup
├── run-docker.sh       Builds and starts with LAN HTTPS
├── TODOS.md            Open work items
└── requirements.txt    Python dependencies
```

## Getting started
Requirements: a Sarvam AI API key; Docker (to test on a phone) or Python 3.9+ (laptop only).

On a phone (mobile browsers need HTTPS for mic and camera):
```bash
git clone https://github.com/abhijha8287/paytm-ai-hackathon.git
cd paytm-ai-hackathon
cp .env.example .env          # set SARVAM_API_KEY
./run-docker.sh               # prints https://localhost:8000 and https://<lan-ip>:8000
```
Accept the self-signed certificate warning once. Stop with `docker compose down`.

Laptop only:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload     # http://127.0.0.1:8000
```

## Configuration
| Variable | Purpose |
|:--|:--|
| `SARVAM_API_KEY` | Speech-to-text, translation, text-to-speech |

## Tech stack
Python, FastAPI, Sarvam AI (Saaras v3, Sarvam-M, Bulbul), JavaScript, jsQR, qrcode.js, Docker

## Using it

1. **Identify the payer**: tap **Scan QR** (uses the camera — any detected
   QR is accepted, nothing is verified) or **Enter UPI ID instead** (any
   non-empty value is accepted). Either way, nothing is sent anywhere.
2. **Set the payer's language** once, top-left ("Payer language: ..."). This
   is a one-time setting, not asked again per transaction.
3. **Tap the mic button** and speak an amount, in any language — no need to
   select which one.
   - If the mic is denied or the amount can't be understood, you're dropped
     straight into a manual amount-entry screen — the flow never dead-ends.
4. The app shows the amount, who the payer is, and speaks a confirmation
   prompt back in the payer's language.
5. Tap **Confirm & Pay**. A local payment reference and a real, scannable
   QR code are generated (nothing external is called here).
6. Use the demo-only **Simulate Success / Simulate Decline** buttons to
   drive the payment to a terminal state, the way a real payment app's
   confirmation would.
7. **Edit amount** goes back to just the amount step (keeps the payer you
   identified). **Change payer** goes back to payer identification only
   (keeps the amount). **Reset demo** (top-right) clears everything and
   starts over — use this to replay the whole demo.

## Notes

- Everything runs locally except calls to the Sarvam AI API and Google
  Fonts (for multi-script typography) — no payment gateway, no other
  external service, no account/dashboard dependency beyond your Sarvam key.
- The QR generator (`static/qrcode.js`) and QR camera decoder
  (`static/jsqr.js`) are both vendored locally — no CDN, no network call.
- Console logging is verbose by design (open your browser's dev tools) —
  every step logs under a `[Sarthi:...]` tag, useful for live debugging.
- See `TODOS.md` for deferred work (accessibility pass) and
  `~/.gstack/projects/paytm-ai-hackathon/` for the full design history.
