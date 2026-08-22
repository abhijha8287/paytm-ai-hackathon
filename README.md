# PAYTM HACKATHON
# Paytm Sarthi — Cross-Language Voice Payment Bridge

A payer is identified first (scan a QR or enter a UPI ID — demo-only, not
verified against anything). Then a merchant speaks an amount out loud in
any language, with no language selection. The payer sees and hears that
amount in their own pre-set language, confirms, and completes a payment —
locally simulated, no external payment gateway involved.

- **Voice, translation, and amount extraction**: real, live — Sarvam AI
  (Saaras v3 speech-to-English + language auto-detect, Sarvam-M as an
  extraction fallback, Bulbul text-to-speech).
- **Payer identification**: demo-only, fully local — a real QR *decoder*
  (camera scan) accepts any detected QR value as-is, or you can type any
  UPI ID. Nothing is validated or sent anywhere.
- **Payment**: a fully local dummy flow — a generated reference ID, a real
  (genuinely scannable) QR code encoding a UPI-style payment string with
  the amount, and a "Simulate Success/Decline" control that drives the
  same success/failure UI a real payment gateway would. No Paytm or any
  other payment provider is involved.

## Run it — two ways

### Option A: Docker (recommended if you want it on your phone)

This is the only way to get the mic and camera working on a phone: mobile
browsers block microphone/camera access on a plain `http://<lan-ip>` — it
has to be `https://` (or `localhost`). The Docker setup generates a
self-signed HTTPS certificate for your machine's actual LAN IP automatically.

```bash
cp .env.example .env      # then edit .env and set SARVAM_API_KEY
./run-docker.sh
```

The script detects your LAN IP, builds the image, and prints the two URLs:

- **On this laptop**: `https://localhost:8000`
- **On your phone** (same wifi): `https://<your-lan-ip>:8000`

Your phone's (and laptop's) browser will show a certificate warning —
that's expected for a self-signed cert; tap **Advanced → Proceed** (Chrome)
or **visit this website** (Safari) once. The connection is still fully
local and encrypted; nothing leaves your network.

To stop it: `docker compose down`

### Option B: Run directly with Python (laptop only)

Camera/mic won't work from a phone this way (plain HTTP) — use this if
you're only testing on the same laptop.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env and set SARVAM_API_KEY
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000**.

## Requirements

- A Sarvam AI API key — get one free at [dashboard.sarvam.ai](https://dashboard.sarvam.ai)
- For Option A: Docker Desktop running
- For Option B: Python 3.9+

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
