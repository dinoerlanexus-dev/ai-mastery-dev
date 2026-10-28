# CS-104 — SLA & Availability Report: Code Does the Math, AI Writes the Story
**Category:** AI Usecase · Operations / Management reporting · Working code
**Date:** 2026-10-26
**Code:** `ai-mastery-dev/03-sla-analyzer/` (`sla_analyzer.py`, `prompts.py`, `data/incidents.csv`)
**Status:** ✅ Working code · tested on Streamlit Cloud (12 Oct 2026) · part of the "Dinoerla NetOps" dashboard

---

## The Problem

**Situation:** Every month the NOC of PT Bank Arunika (fictional) must tell management whether the
network met its SLA (Service Level Agreement) — and why not.

**Pain points from the field:**
- Availability, MTTR (Mean Time To Repair) and error budget are calculated by hand in spreadsheets
- Management doesn't read "99.9352%" — they want "are we OK, what broke, what are we doing about it"
- Asking a generic AI to "analyse my incidents" is risky: **LLMs are bad at arithmetic** and will
  confidently produce wrong availability numbers

---

## The Design Principle — "hands + brain"

| Layer | Who | Why |
|---|---|---|
| Arithmetic (availability, MTTR, error budget, breach) | **CODE** (Python) | Deterministic, auditable, always the same answer |
| Narrative (what it means, top contributors, actions) | **AI** (Gemini) | Language and synthesis |
| Guardrail | Prompt: *"Numbers are already computed — do NOT recalculate or invent numbers"* | Keeps AI out of the math |

Analogy: the router counts interface errors; the engineer explains them to management.
You would never ask the engineer to recount packets by hand.

---

## The Scenario (synthetic data, `data/incidents.csv`)

| Start | Duration | Severity | Description |
|---|---|---|---|
| 03 Aug 02:10 | 12 min | High | BGP flap Gi0/1 BR-JKT-03 (CRC / Layer 1) |
| 11 Aug 14:05 | 4 min | Medium | OSPF adjacency drop core-01 |
| 18 Aug 09:14 | 5 min | High | Interface flap + BGP hold expired BR-JKT-03 |
| 24 Aug 21:40 | 7 min | Low | Latency spike WAN Surabaya |

Settings: SLA target **99.99%**, period **30 days**.

---

## The Result (computed by code — verifiable by hand)

| Metric | Value | Check |
|---|---|---|
| Period | 43,200 min | 30 × 24 × 60 |
| Total downtime | 28 min | 12 + 4 + 5 + 7 |
| Availability | **99.9352%** | (43,200 − 28) / 43,200 |
| MTTR | 7.0 min | 28 / 4 incidents |
| Error budget (99.99%) | 4.32 min | 43,200 × 0.0001 |
| Error budget used | **648% → BREACH** | 28 / 4.32 |

**The insight a human would want surfaced:** one device, **BR-JKT-03, caused 17 of the 28 minutes (~61%)**
in two incidents with the same Layer-1 signature (CRC errors → BGP flap). That's a circuit/optics
problem, not a routing-design problem — fix the link, and most of the breach disappears.

The AI report is asked to cover: status (breach/OK) · business interpretation · top contributors ·
recommendations to cut MTTR · compliance note (general OJK/BI availability & BCM principles, article numbers marked "(verify)").

---

## Business Value — hypotheses to measure in a pilot

| Metric | How to measure |
|---|---|
| Monthly report preparation time | Hours before vs after, same month's data |
| Number errors in reports | Code-computed → expected zero; audit a sample |
| Management readability | Ask the readers: can they state status + top action after 1 minute? |

---

## Honest Limitations (and next steps)

1. Every incident counts as **full outage** of one service — no partial degradation, no per-service weighting.
2. Period and target are constants in the code; a real report needs per-service SLA contracts.
3. Input is a hand-made CSV. Next: pull incidents straight from Jira (the n8n pipeline in CS-106 already has them).
4. Compliance note is general; a grounded version would reuse the OJK RAG (CS-105). Planned as n8n v2.

---

## Demo Script (interview / client meeting)

*"I never let the AI do the arithmetic. The code calculates availability, MTTR and error budget —
the numbers are exact and auditable. The AI only writes the management narrative, and the prompt
forbids it from changing or inventing numbers.*

*In this example the network breached a 99.99% SLA — 648% of the error budget used. But the useful part
is the story behind it: one branch router with a bad circuit caused 61% of the downtime.
That's the sentence a CIO needs, and that's where my domain experience comes in."*

---

## Files

- Code: `03-sla-analyzer/` · smoke tests: `test_sla_analyzer.py`
- Screenshots: `03-sla-analyzer/deliverables/`
- Related: CS-105 (OJK grounding), CS-106 (incidents from Jira)

*AI Mastery Program · Dili Noerlan · 2026-10-26*
