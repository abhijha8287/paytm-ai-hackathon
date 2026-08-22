# TODOS

## Paytm Sarthi

### Full accessibility pass (keyboard nav, ARIA, screen reader)

**What:** Add keyboard navigation, ARIA landmarks/labels, and screen-reader
support across both screens (merchant recording, payer confirmation).

**Why:** A real shipped product needs this; a presenter-operated,
voice-first stage demo on one device doesn't have an audience that benefits
from it. Deferring it was a proportionality call, not an oversight.

**Context:** Decided during /plan-design-review (Pass 6: Responsive &
Accessibility) on 2026-08-22. Touch target sizing (44px min) and color
contrast (4.5:1) ARE already locked into the design doc regardless — only
keyboard nav and screen-reader support were deferred. See the design doc's
"Responsive & Accessibility" section for what's already covered:
`~/.gstack/projects/paytm-ai-hackathon/abhishek-unknown-design-20260822-123028.md`

**Effort:** M — keyboard nav and ARIA labeling across two screens plus the
error/success state variants from the Interaction States table.
**Priority:** P3
**Depends on:** None.
