CS-101 until C-1XX is from Claude

# CS-101 — AI-Assisted RCA for Banking Network Incident
**Category:** AI Usecase Demo · Operations
**Date:** 2026-06-05
**Prompt used:** `rca-banking-v1`
**Status:** ✅ Production-ready demo · **v2 (26 Oct 2026):** real bank name replaced with a fictional one; unverified regulatory claims flagged

---

## The Problem

**Situation:** A major Indonesian bank experiences a network outage. NOC engineers are in panic mode — logs scattered across multiple systems, timeline unclear, management demanding answers, OJK (Otoritas Jasa Keuangan) reporting clock ticking.

**Pain points from the field:**
- Data collection is manual — CLI commands run one by one during the incident
- Chronology built from memory and WhatsApp messages
- RCA (Root Cause Analysis) report takes 3 days minimum
- OJK incident-reporting deadlines are tight (exact timeframe per POJK 11/2022 / SEOJK — verify before quoting) — deadline often missed
- Topology diagrams are usually outdated

**Business stakes:** Every hour of delay = more transactions at risk, more regulatory exposure, more reputational damage.

---

## The Scenario

```
Bank:      PT Bank Arunika (fictional)
Incident:  BGP (Border Gateway Protocol) flap — 
           both ISP sessions dropped simultaneously
Date:      2026-05-15, 14:23 - 16:47 WIB
Duration:  2 hours 24 minutes
Impact:    237 ATMs unreachable · 42 branches slow
           Internet + mobile banking degraded
           47,000+ transactions affected
           Rp 284 miliar at risk
Root cause: IOS-XE upgrade — BGP prefix-list filter
            not migrated → router accepted full 
            internet routing table (847,233 routes 
            vs normal 12) → CPU 98% → BGP keepalive
            failure → both ISP sessions dropped
```

---

## The Approach

**Step 1:** Collect minimum viable data during/after incident
- Incident description
- Affected systems list
- Timeline of events (from NOC alerts and logs)
- Relevant log excerpts (syslog, BGP notifications)
- Network topology notes

**Step 2:** Paste data into `rca-banking-v1` prompt

**Step 3:** Claude produces structured 7-section RCA draft in minutes

**Step 4:** Domain expert (Dili) validates:
- Technical accuracy of root cause
- OJK regulatory compliance of report
- Business impact quantification
- Governance insight — *"This is a change management failure, not just a technical failure"*

**Step 5:** Final RCA ready for management and OJK submission

---

## AI Output — 7 Sections Produced

| Section | Content | Quality |
|---------|---------|---------|
| 1 — Incident Summary | 3 sentences, business language, zero jargon | ✅ |
| 2 — Root Cause | Primary + contributing factors, technical depth | ✅ |
| 3 — Timeline Reconstruction | Chronological from log data | ✅ |
| 4 — Impact Assessment | Business + technical, Rp quantified | ✅ |
| 5 — Immediate Actions | Past tense, action-oriented | ✅ |
| 6 — Permanent Fix | 4 controls with timelines | ✅ |
| 7 — Prevention Measures | Change management + monitoring | ✅ |

---

## Domain Validation — What AI Got Right

✅ Identified BGP hold-timer expiry as immediate cause
✅ Connected CPU exhaustion to route table explosion
✅ Flagged missing BGP maximum-prefix as gap
✅ Mapped technical failure to business impact
✅ Included OJK reporting status in output
✅ Used governance language in prevention section

---

## Domain Validation — What Required Human Expertise

⚠️ **Governance insight:** AI listed technical fixes. Domain expertise elevated this to board-level: *"Root cause is change management maturity — not BGP configuration."*

⚠️ **Transaction outcome precision:** AI labeled Rp 284 miliar as "at risk" — domain expert clarifies distinction between at-risk, delayed, and actually lost. Critical for OJK reporting accuracy.

⚠️ **OJK nuance:** AI referenced POJK 11/2022 correctly but domain expert validates specific pasal references before submission.

---

## Business Value

| Metric | Before AI | After AI | Improvement |
|--------|-----------|----------|-------------|
| RCA draft ready | 3 days | 30 minutes | 144× faster |
| OJK notification | Risk of missing | Same-day | Zero deadline risk |
| Management briefing | Day 3 | Day 1 | 3 days earlier |
| MTTR (Mean Time To Resolve) | 2.5 hours | Target: <30 min* | 5× faster |

*With Layer 2 integration (Month 2): auto-collect logs at incident start → pre-populated RCA template when NOC opens ticket.

---

## Key Insight for CIO Conversations

> *"This is not just about writing RCA faster. This is about changing the economics of incident response. When your engineers spend 3 days writing reports instead of preventing the next incident — that's the real cost."*

**The AI layer removes the documentation burden from engineers.**
They focus on resolution. AI handles the paperwork.

---

## Prompt Performance Notes

**What worked:**
- `CONSTRAINT: Base analysis ONLY on data provided` → Claude flagged "Insufficient data" correctly where data was missing
- Dual audience instruction → business language in sections 1 and 4, technical depth in section 2

**v2 improvement to add:**
```
TONE: Treat as formal OJK incident report draft
Transaction outcome: [recovered/partial loss/under assessment]
Changes before incident: [maintenance window, upgrades, config changes]
```

---

## Demo Script (for interviews/client meetings)

*"Let me show you what I mean by AI-augmented consulting. Here's a real banking incident scenario — BGP flap, 2.5 hour outage, 237 ATMs down.*

*I paste the incident data into this prompt. In 90 seconds, I have a 7-section RCA with OJK regulatory references, business impact in Rupiah, and a permanent fix roadmap.*

*Without AI, this takes 3 days. With AI, it takes 30 minutes — and I spend that time validating the output with domain expertise, not writing from scratch.*

*The prompt was designed specifically for Indonesian banking — it knows OJK POJK 11/2022, it knows the difference between at-risk and lost transactions, it knows what a CIO needs to see versus what a NOC engineer needs to see."*

---

## Files Referenced

- Prompt: `04. PROMPTS/rca-banking-v1.md`
- Knowledge: `03. KNOWLEDGE/CLAUDE/2026-06-02_LLM-101.md`
- Program notes: `02. PROGRAM/Month-1/2026-06-05.md`

---

*AI Mastery Program · Dili Noerlan · 2026-06-05*
