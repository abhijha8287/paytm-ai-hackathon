"""
Paytm Sarthi - Cross-Language Voice Payment Bridge (hackathon build)

Design doc: ~/.gstack/projects/paytm-ai-hackathon/abhishek-unknown-design-20260822-144937.md

Flow: merchant speaks an amount (any language, auto-detected) -> Sarvam Saaras
translates + extracts -> payer hears/sees it in their own pre-set language ->
confirms -> a fully local dummy payment is created and simulated to
completion. No external payment gateway integration of any kind - the only
external network dependency in this app is the Sarvam AI API.
"""

import functools
import os
import random
import re
import string
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sarvamai import AsyncSarvamAI

# --------------------------------------------------------------------------
# Config / clients
# --------------------------------------------------------------------------

load_dotenv()

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")

sarvam_client = AsyncSarvamAI(api_subscription_key=SARVAM_API_KEY) if SARVAM_API_KEY else None

app = FastAPI(title="Paytm Sarthi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# In-memory single-transaction state (Premise 5: no DB, no auth)
# --------------------------------------------------------------------------

TRANSACTION: dict = {}


def reset_transaction() -> None:
    TRANSACTION.clear()
    TRANSACTION.update(
        {
            "amount": None,
            "payment_created": False,
            "order_id": None,
            "short_url": None,
            "long_url": None,
            "status": None,  # None | "pending" | "success" | "decline" | "timeout"
            "created_at": None,
        }
    )


reset_transaction()

# --------------------------------------------------------------------------
# Shared error-handling helper (eng review: one place for the toast contract)
# --------------------------------------------------------------------------


def external_call(step: str):
    """Wraps a handler that talks to an external service (Sarvam). Logs to console (for live
    debugging on stage) and returns a structured {"error": ...} the frontend
    renders as a calm-neutral toast, instead of a raw 500."""

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - deliberately broad, this is the one place we catch
                print(f"[{step}] error: {exc!r}")
                return JSONResponse(
                    status_code=502,
                    content={"error": True, "step": step, "message": str(exc)},
                )

        return wrapper

    return decorator


# --------------------------------------------------------------------------
# Amount extraction: regex -> Sarvam-M LLM fallback -> manual (frontend)
# --------------------------------------------------------------------------

_WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_WORD_MULTIPLIERS = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lac": 100000}


def _parse_word_number(text: str) -> Optional[int]:
    """Parses simple English number-word phrases like 'three hundred' or
    'two thousand five hundred'. Returns None if it can't confidently parse."""
    tokens = re.findall(r"[a-z]+", text.lower())
    total = 0
    current = 0
    matched_any = False
    for tok in tokens:
        if tok in _WORD_NUMBERS:
            current += _WORD_NUMBERS[tok]
            matched_any = True
        elif tok in _WORD_MULTIPLIERS:
            multiplier = _WORD_MULTIPLIERS[tok]
            current = (current or 1) * multiplier
            total += current
            current = 0
            matched_any = True
        elif tok == "and":
            continue
    total += current
    return total if matched_any and total > 0 else None


_CURRENCY_MARKED_RE = re.compile(
    r"(?:rs\.?|inr|₹)\s*([\d]+(?:,\d{3})*(?:\.\d+)?)|([\d]+(?:,\d{3})*(?:\.\d+)?)\s*(?:rs\.?|rupees?|rupaye)",
    re.IGNORECASE,
)
_BARE_DIGIT_RE = re.compile(r"\b\d{1,7}(?:,\d{3})*(?:\.\d+)?\b")


def extract_amount_regex(text: str) -> Optional[float]:
    """Layer 1: digit amounts ('300', '₹300', '300 rupees') and simple
    word-numbers ('three hundred').

    A currency-marked digit run (₹/Rs/rupees adjacent to the number) is
    trusted at any length. A BARE digit run with no currency marker is only
    accepted if it's amount-shaped (<=7 digits) — otherwise something like
    a spoken phone number ("9840950950") gets misread as an amount, which
    is exactly the kind of adversarial case this layer needs to decline
    rather than guess at (falls through to the Sarvam-M layer instead)."""
    marked = _CURRENCY_MARKED_RE.search(text)
    if marked:
        raw = (marked.group(1) or marked.group(2)).replace(",", "")
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass

    bare = _BARE_DIGIT_RE.search(text)
    if bare:
        raw = bare.group(0).replace(",", "")
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass

    word_value = _parse_word_number(text)
    if word_value:
        return float(word_value)

    return None


async def extract_amount_llm(text: str) -> Optional[float]:
    """Layer 2: Sarvam-M chat fallback. Strict prompt, digits-only reply."""
    if sarvam_client is None:
        return None
    prompt = (
        "Extract only the numeric rupee amount from this text. "
        "Reply with digits only, no currency symbol, no words, no explanation. "
        "If no amount is found, reply exactly: NONE\n\n"
        f"Text: {text}"
    )
    response = await sarvam_client.chat.completions(
        messages=[{"role": "user", "content": prompt}],
        model="sarvam-105b",  # the Sarvam-M chat model's current model literal
    )
    reply = response.choices[0].message.content.strip()
    if reply.upper() == "NONE":
        return None
    digits = re.sub(r"[^\d.]", "", reply)
    try:
        value = float(digits)
        return value if value > 0 else None
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Local dummy payment
# --------------------------------------------------------------------------


def generate_order_id() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SARTHI{int(time.time())}{suffix}"


async def create_local_payment(amount: float) -> dict:
    """Generates a fully local dummy payment - no external network call, no
    payment gateway of any kind. order_id/reference is locally generated;
    completion is simulated via /simulate-result + /check-status below."""
    order_id = generate_order_id()
    reference = f"https://sarthi.demo/pay/{order_id}"
    print(f"[create-payment] local dummy payment created for order {order_id}")
    return {"order_id": order_id, "short_url": reference, "long_url": reference}


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transcribe")
@external_call("transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Step 3+4+5: mic capture already happened client-side. This endpoint
    does ASR+translate+language-detect in ONE Sarvam call (Saaras v3,
    mode='translate', language_code='unknown' - see design doc Premise 1),
    then runs the 3-layer amount extraction chain (regex -> Sarvam-M -> the
    frontend's manual input is the 3rd layer, triggered when this returns
    amount: null)."""
    if sarvam_client is None:
        return JSONResponse(
            status_code=503,
            content={"error": True, "step": "transcribe", "message": "SARVAM_API_KEY not configured"},
        )

    audio_bytes = await audio.read()

    result = await sarvam_client.speech_to_text.transcribe(
        file=(audio.filename or "audio.webm", audio_bytes),
        model="saaras:v3",
        mode="translate",
        language_code="unknown",
    )
    translated_text = getattr(result, "transcript", "") or ""
    detected_language = getattr(result, "language_code", None)

    amount = extract_amount_regex(translated_text)
    source = "regex" if amount is not None else None

    if amount is None:
        amount = await extract_amount_llm(translated_text)
        source = "llm" if amount is not None else None

    return {
        "transcript": translated_text,
        "detected_language": detected_language,
        "amount": amount,
        "amount_source": source,  # "regex" | "llm" | None (frontend falls to manual input)
    }


@app.post("/speak")
@external_call("speak")
async def speak(text: str = Form(...), language_code: str = Form(...)):
    """TTS confirmation prompt in the payer's pre-set language (Bulbul)."""
    if sarvam_client is None:
        return JSONResponse(
            status_code=503,
            content={"error": True, "step": "speak", "message": "SARVAM_API_KEY not configured"},
        )

    result = await sarvam_client.text_to_speech.convert(
        text=text,
        language_code=language_code,
        model="bulbul:v2",
    )
    audio_b64 = result.audios[0] if getattr(result, "audios", None) else None
    if audio_b64 is None:
        return JSONResponse(
            status_code=502,
            content={"error": True, "step": "speak", "message": "No audio returned"},
        )
    return {"audio_base64": audio_b64}


@app.post("/create-payment")
@external_call("create-payment")
async def create_payment(amount: float = Form(...)):
    """Step 7: fully local dummy payment (see create_local_payment) - no
    external payment gateway. Guarded against double-tap (eng review
    finding 6) - one payment reference per transaction, no matter how many
    times this is hit."""
    if TRANSACTION.get("payment_created"):
        return {
            "order_id": TRANSACTION["order_id"],
            "short_url": TRANSACTION["short_url"],
            "long_url": TRANSACTION["long_url"],
            "already_created": True,
        }

    link = await create_local_payment(amount)

    TRANSACTION.update(
        {
            "amount": amount,
            "payment_created": True,
            "order_id": link["order_id"],
            "short_url": link["short_url"],
            "long_url": link["long_url"],
            "status": "pending",
            "created_at": time.time(),
        }
    )

    return {
        "order_id": link["order_id"],
        "short_url": link["short_url"],
        "long_url": link["long_url"],
        "already_created": False,
    }


@app.post("/simulate-result")
async def simulate_result(status: str = Form(...)):
    """Demo-only control that drives the local dummy payment to a terminal
    state. status: 'success' | 'decline'"""
    if status not in ("success", "decline"):
        return JSONResponse(status_code=400, content={"error": True, "message": "status must be success or decline"})
    if not TRANSACTION.get("payment_created"):
        return JSONResponse(status_code=400, content={"error": True, "message": "no payment created yet"})
    TRANSACTION["status"] = status
    return {"status": status}


@app.get("/check-status")
async def check_status():
    """Reads the local dummy payment's status, driven by /simulate-result.
    60s cap: if still 'pending' after 60s with no simulate-result call,
    report 'timeout'."""
    if not TRANSACTION.get("payment_created"):
        return JSONResponse(status_code=400, content={"error": True, "message": "no payment created yet"})

    status = TRANSACTION.get("status")
    if status == "pending" and TRANSACTION.get("created_at"):
        elapsed = time.time() - TRANSACTION["created_at"]
        if elapsed > 60:
            status = "timeout"

    return {"status": status, "order_id": TRANSACTION.get("order_id")}


@app.post("/reset")
async def reset():
    """Demo-only: clears the in-memory transaction so a rehearsal run or an
    encore doesn't require restarting the server mid-event."""
    reset_transaction()
    return {"status": "reset"}


# Serve the frontend (single index.html, vanilla JS - no build step)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
