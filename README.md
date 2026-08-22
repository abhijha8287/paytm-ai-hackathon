# Paytm Sarthi — Cross-Language Voice Payment Bridge

A merchant speaks an amount out loud in any language, with no language
selection. A payer sees and hears that amount in their own pre-set
language, confirms, and completes a payment — locally simulated, no
external payment gateway involved.

- **Voice, translation, and amount extraction**: real, live — Sarvam AI
  (Saaras v3 speech-to-English + language auto-detect, Sarvam-M as an
  extraction fallback, Bulbul text-to-speech).
- **Payment**: a fully local dummy flow — a generated reference ID, a
  locally-rendered QR-style graphic, and a "Simulate Success/Decline"
  control that drives the same success/failure UI a real payment gateway
  would. No Paytm or any other payment provider is involved.

## Requirements

- Python 3.9+
- A Sarvam AI API key — get one free at [dashboard.sarvam.ai](https://dashboard.sarvam.ai)

## Setup

```bash
# from the project directory
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Open `.env` and set:

```
SARVAM_API_KEY=your_key_here
```

## Run

```bash
source .venv/bin/activate          # if not already active
uvicorn main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser (a phone browser works
too — resize the window or open it on your phone if it's on the same
network as your laptop, e.g. `http://<your-laptop-ip>:8000`).

## Using it

1. **Set the payer's language** once, top-left ("Payer language: ..."). This
   is a one-time setting, not asked again per transaction.
2. **Tap the mic button** and speak an amount, in any language — no need to
   select which one.
   - If the mic is denied or the amount can't be understood, you're dropped
     straight into a manual amount-entry screen — the flow never dead-ends.
3. The app shows the amount and speaks a confirmation prompt back in the
   payer's language.
4. Tap **Confirm & Pay**. A local payment reference and QR-style code are
   generated (nothing external is called here).
5. Use the demo-only **Simulate Success / Simulate Decline** buttons to
   drive the payment to a terminal state, the way a real payment app's
   confirmation would.
6. **Reset demo** (top-right) clears the transaction so you can replay the
   demo without restarting the server.

## Notes

- Everything runs locally except calls to the Sarvam AI API and Google
  Fonts (for multi-script typography) — no payment gateway, no other
  external service, no account/dashboard dependency beyond your Sarvam key.
- Console logging is verbose by design (open your browser's dev tools) —
  every step logs under a `[Sarthi:...]` tag, useful for live debugging.
- See `TODOS.md` for deferred work (accessibility pass) and
  `~/.gstack/projects/paytm-ai-hackathon/` for the full design history.
