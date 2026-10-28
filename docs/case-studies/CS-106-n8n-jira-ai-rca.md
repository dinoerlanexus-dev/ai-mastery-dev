# CS-106 — AI RCA Inside the Ticket Flow: AI Drafts, Humans Verify, Automation Publishes
**Category:** AI Usecase · Operations automation · Working workflows
**Date:** 2026-10-26
**Code:** `ai-mastery-dev/05-n8n-jira-rca/` (`wf-0-error-notifier.json`, `wf-1-rca-v1.1.json`, `wf-2-exec-summary.json`)
**Status:** ✅ LIVE on laptop (n8n 2.42.6) · end-to-end demo from a phone on 21 Oct 2026

---

## The Problem

**Situation:** The NOC of PT Bank Arunika (fictional) runs incidents in an ITSM (IT Service Management)
tool — here Jira Service Management. Every incident needs (1) a first technical analysis and
(2) a short management summary.

**Pain points from the field:**
- The first analysis takes long and depends on who is on shift
- Management summaries are written last, after the incident, often late
- Most AI demos are a separate chatbot — engineers won't leave their ticket tool to use it
- Banks won't accept AI posting conclusions on its own, or AI text visible to customers

---

## The Design — three workflows, one state machine in the ticket label

```
Engineer adds label  ai-rca
        │
WF-1  (poll every 5 min) → filter 3 fields → Gemini RCA draft
        → INTERNAL note 🔒 on the ticket → label ai-rca-draft
        │
Engineer reviews the draft, writes the verified cause as an internal note,
changes label → ai-rca-verified          ← human gate
        │
WF-2  (poll every 5 min) → read ALL comments, tag [AI DRAFT] / [ENGINEER]
        → Gemini executive summary in Bahasa Indonesia ([ENGINEER] overrides AI)
        → INTERNAL note 🔒 "RINGKASAN EKSEKUTIF – FINAL" → label ai-rca-final

WF-0  any failure in WF-1 / WF-2 → email: workflow, node, error, link to the run
```

| Design choice | Why | Network analogy |
|---|---|---|
| AI lives **inside the ticket** | No new tool to learn | — |
| Label = state; workflows don't talk directly | Each workflow can fail without breaking the other | Two routers sharing state via BGP community |
| Polling, not webhook | Laptop sits behind NAT | SNMP poll vs trap |
| Only 3 fields reach the AI | Less data exposure, cheaper | ACL — and the masking point |
| Internal note (`sd.public.comment {internal:true}`) | Customers never see AI drafts | — |
| AI never sets `verified` | A human signs off | Change approval before commit |
| Label changes only **after** the note is posted | No "done" label on a failed run | Don't clear the alarm before the ticket exists |
| Retry 3× on Gemini; ticket stays queued on failure | Gemini returned 503 several times in one week | BGP connect-retry |

---

## The Proof — NO-3 (SD-WAN failover not triggering)

| Step | What happened |
|---|---|
| AI draft (WF-1) | Candid: **"Insufficient data", confidence Low** — asked for BFD session, SLA probe and vSmart policy data |
| Engineer note | *BFD on the MPLS TLOC stayed up because hellos partially passed; packet loss stayed below the SLA-class threshold, so AAR never triggered failover. Threshold adjusted, failover to broadband succeeded.* |
| Executive summary (WF-2) | Bahasa Indonesia, 5 points (what happened · business impact · **verified root cause = the engineer's** · status · prevention). Ran in 42 s, 7 nodes, from a label change on a phone. |

**The story in one line:** the AI gave structure and honesty, the expert gave the insight,
automation turned it into a board-ready summary.

Other evidence: NO-2 (ACI contract missing TCP 1521) went through the same cycle on 20 Oct.

---

## Reliability — tested on purpose

| Test | Result |
|---|---|
| Fault test: JQL with a non-existent project (`NOPE`) | Jira returned 0 tickets, **no error** → a typo can stay silent. Lesson: needs a heartbeat |
| Fault test: JQL syntax error | Error email in under 1 minute, link opened the failed run |
| Real Gemini 503 (20 Oct) | Retries exhausted → email → ticket stayed `ai-rca` → processed automatically when Gemini recovered (21 Oct) |
| Idea "turn off Wi-Fi to test alarms" | Rejected: the email would fail with the link (**fate-sharing**) → why out-of-band management exists |

---

## Business Value — hypotheses to measure in a pilot

| Metric | How to measure |
|---|---|
| Time to first analysis | Ticket opened → first structured RCA note, before vs after |
| Time to management summary | Incident resolved → summary sent |
| Draft usefulness | % of drafts accepted with minor edits by the engineer |
| Cost per ticket | AI calls × price (2 calls per ticket in this flow) — verify current pricing |

---

## Honest Limitations (backlog v1.2 / v2)

- Single model (Gemini) → add a **fallback model** when it returns 503
- Every failed poll emails → **rate-limit alarms** (one per incident, not one per poll)
- Drafts can be over-cautious → prompt for **ranked hypotheses** with confidence even when data is thin
- All comments are posted under the engineer's account → a **bot account** for clean audit trail
- Runs on a laptop → production: n8n on a managed host / Docker, Vertex AI in an approved region (verify)
- Planned v2: OJK citations (CS-105) and SLA impact (CS-104) inside the same ticket

---

## Demo Script (interview / client meeting)

*"Your NOC already lives in the ticketing tool, so I put the AI there. An engineer adds one label.
Within five minutes an AI draft appears as an internal note — customers can't see it.
The engineer corrects it and marks it verified. Five minutes later the management summary appears
in Bahasa Indonesia, built from the engineer's version, not the AI's.*

*The AI never decides. It drafts. A human verifies. Automation publishes.
And when the AI provider goes down, nothing is lost — the ticket waits and the team gets an alert."*

---

## Files

- Workflows: `05-n8n-jira-rca/` (audited: no tokens, no test data)
- Screenshots: `docs/images/` (AI draft, executive summary, n8n run)
- Related: CS-101 (RCA prompt), CS-103 (executive summary), CS-104, CS-105

*AI Mastery Program · Dili Noerlan · 2026-10-26*
