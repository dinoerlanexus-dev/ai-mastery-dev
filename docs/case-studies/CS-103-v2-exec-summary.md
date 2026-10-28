# CS-103 — AI-Assisted Executive Summary Generation
**Category:** AI Usecase Demo · Communications
**Date:** 2026-06-10
**Prompt used:** `exec-summary-v1`
**Status:** ✅ Production-ready demo · **v2 (26 Oct 2026):** real bank name replaced with a fictional one; unverified regulatory claims flagged

---

## The Problem

**Situation:** Banking incident resolved. NOC team produces a 10-page technical RCA. CISO needs to brief the Board of Directors and submit to OJK (Otoritas Jasa Keuangan) — today. The technical report is accurate but unreadable for C-suite. Translation takes 4 hours minimum by a senior consultant.

**Pain points from the field:**
- Technical RCA language is incomprehensible to Board and regulators
- Translation requires senior person — expensive, scarce resource
- Under time pressure, quality suffers — important nuances get lost
- OJK submission format requires specific structure — easy to miss elements
- Business impact gets under/over-stated — both are dangerous

**Business stakes:** Board makes decisions based on executive summaries. Inaccurate or incomplete summaries = wrong decisions. OJK submission errors = regulatory risk.

---

## The Scenario

```
Bank:      PT Bank Arunika (fictional)
Request:   CISO needs executive summary from 
           technical RCA — for Direktur IT and OJK
Deadline:  2 hours from now
Input:     Full technical RCA (BGP flap incident)
Audience:  Direktur IT + OJK regulators
Purpose:   Internal board briefing + OJK regulatory 
           reporting
```

---

## The Approach

**Step 1:** Take completed technical RCA from NOC team

**Step 2:** Paste into `exec-summary-v1` prompt with:
- Incident date/duration
- Full technical report
- Target audience specification
- Purpose (internal/OJK/board)

**Step 3:** Claude produces 1-page executive summary in minutes

**Step 4:** Domain expert validates:
- Zero technical jargon leaked through
- Business impact accurately stated
- OJK regulatory status correct
- Governance language appropriate for board
- Transaction outcome precision (at-risk vs lost vs delayed)

---

## AI Output — 7-Section Executive Summary

| Section | What Claude Produced | Quality |
|---------|---------------------|---------|
| 1 — Incident Overview | 3 sentences, business language, zero jargon | ✅ Clean |
| 2 — Business Impact | Rp 284B at risk · 47,000+ transactions · 237 ATMs | ✅ Quantified |
| 3 — Root Cause | *"Like a post office suddenly receiving all national mail"* analogy | ✅ Memorable |
| 4 — What We Did | Action-oriented, past tense, clear timeline | ✅ Accountable |
| 5 — What We Are Doing | 4 permanent controls with specific timelines | ✅ Forward-looking |
| 6 — Regulatory Status | OJK Submitted ✅  ·  Full report Pending ⏳ | ✅ Board-ready |
| 7 — Assurance Statement | Change management procedures updated | ✅ **Governance language** |

---

## The Governance Insight

**What NOC wrote in technical RCA:**
> *"BGP prefix-list filter configuration was not migrated correctly during IOS-XE upgrade from 17.3.4 to 17.6.1"*

**What Claude produced for the Board:**
> *"The configuration gap that caused this incident has been closed; automated safeguards now prevent any recurrence of this specific failure mode, and the bank's change management procedures have been updated to detect similar risks before any future maintenance activity is approved."*

**What this means:**
Claude elevated the technical finding to governance language — without being told explicitly. The prompt constraint *"zero technical jargon, audience has zero technical background"* forced this elevation.

**Domain expert validation:**
> *"Root cause is not BGP — root cause is change management maturity. The prompt captured this correctly. This is what the Board needs to hear, not prefix-list details."*

---

## Domain Validation — Human vs AI

| Element | AI (Claude) | Domain Expert (Dili) |
|---------|-------------|---------------------|
| Remove technical jargon | ✅ Zero leaked | Verified |
| OJK regulatory status | ✅ Submitted/Pending flags | Validates pasal reference |
| Governance language | ✅ Captured | Elevated to board narrative |
| Root cause analogy | ✅ Post office — memorable | Approved — CIO-appropriate |
| Transaction outcome | ⚠️ "At risk" — ambiguous | **Flagged: at-risk vs lost distinction** |
| Rp quantification | ✅ Draft | Validates source data accuracy |
| Tone — calm, accountable | ✅ | Verified for OJK register |

---

## The Transaction Outcome Gap — Important

Claude flagged this self-critique:

> *"Rp 284 miliar is labeled 'at risk' — but was any of it actually lost, delayed, or fully recovered? A board audience will ask."*

**This is valid and critical for banking.** The distinction matters:

| Outcome | Meaning | OJK Implication |
|---------|---------|-----------------|
| At risk | Transaction attempted during outage | May have been retried successfully |
| Delayed | Transaction completed but late | SLA breach — reportable |
| Lost | Transaction failed permanently | Customer claim — regulatory action |
| Under assessment | Investigation ongoing | Interim report acceptable |

**Action added to `rca-banking-v1` prompt:**
```
Transaction outcome:
[ ] Fully recovered (all retried successfully)
[ ] Partial loss (X% failed permanently)
[ ] Under assessment (investigation ongoing)
```

---

## Business Value

| Metric | Before AI | After AI | Improvement |
|--------|-----------|----------|-------------|
| Exec summary from RCA | 4 hours | 15 minutes | 16× faster |
| Jargon-free quality | Inconsistent | Consistent | Standardized |
| OJK format compliance | Engineer-dependent | Auto-structured | Zero missed fields |
| Board-ready document | Senior consultant only | Any analyst + AI | Democratized |
| Turnaround to Board | Next day | Same day | 24 hours faster |

---

## The Multiplier Effect — All 3 Usecases Combined

When RCA + Config Review + Exec Summary work together:

```
Incident occurs
      ↓
AI-assisted RCA — 30 min (CS-001)
      ↓  
Domain expert validates — 15 min
      ↓
Exec Summary generated — 15 min (CS-103)
      ↓
OJK notification ready — same day ✅
Board briefing ready — same day ✅
      ↓
Config review triggered — 5 min per device (CS-002)
      ↓
Remediation plan with OJK references — same week ✅

Total time: Hours, not weeks.
```

---

## Key Insight for C-Suite Conversations

> *"Every time your bank has an incident, three things need to happen simultaneously: resolve it, report it to OJK, and brief the Board. Right now, your team does those three things sequentially — resolve first, then spend days on paperwork.*
>
> *With AI, all three happen in parallel. Resolution stays human-driven. Documentation becomes AI-accelerated. Your team focuses on fixing, not writing.*
>
> *And the quality is better — because AI doesn't get tired at 2 AM during an incident bridge call."*

---

## Prompt Performance Notes

**What worked:**
- `FORMAT: 7 specific sections` → predictable, reusable output
- `CONSTRAINT: zero technical acronyms` → held perfectly
- `Tone: calm, factual, accountable — not defensive` → board-appropriate register
- Dual purpose spec (internal + OJK) → appropriate formality level

**v2 improvement to add:**
```
TONE: Treat as formal OJK incident report draft — 
      formal register required
TRANSACTION OUTCOME: [recovered/partial/under assessment]
AUDIENCE LEVEL: [Board/CIO/OJK/All]
```

---

## Demo Script (for interviews/client meetings)

*"Here's the final piece of the AI-assisted incident response workflow. I have a 10-page technical RCA from the NOC team. The CISO needs to brief the Board and submit to OJK — in 2 hours.*

*I paste the technical report into this prompt. In 15 minutes, I have a 1-page executive summary: zero jargon, business impact in Rupiah, OJK regulatory status with submitted/pending flags, and a governance assurance statement that the Board can act on.*

*Notice section 7 — Assurance. Claude wrote: 'The bank's change management procedures have been updated.' That's governance language. Not technical language. The Board hears accountability, not excuses.*

*Without AI, this takes 4 hours from a senior consultant. With AI, 15 minutes — and I spend that time validating accuracy, not writing from scratch."*

---

## Complete Demo Portfolio Summary

| Case Study | Prompt | Time Saved | Audience |
|-----------|--------|------------|----------|
| CS-001 RCA | `rca-banking-v1` | 3 days → 30 min | NOC + Management |
| CS-002 Config Review | `config-review-ojk-v1` | 2 days → 5 min | CISO + Audit |
| CS-103 Exec Summary | `exec-summary-v1` | 4 hours → 15 min | Board + OJK |

**Combined value proposition:**
> *"Three tools. Three audiences. One AI-augmented consultant who bridges all of them — with 25 years of domain proof."*

---

## Files Referenced

- Prompt: `04. PROMPTS/exec-summary-v1.md`
- Related: `09. CASE STUDIES/CS-001-RCA-banking.md`
- Program notes: `02. PROGRAM/Month-1/2026-06-10.md`

---

*AI Mastery Program · Dili Noerlan · 2026-06-10*
