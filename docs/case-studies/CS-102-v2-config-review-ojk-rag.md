# CS-102 v2 — Config Compliance Review, Grounded in Real OJK Text (RAG)
**Category:** AI Usecase · Compliance · Working code
**Date:** 2026-10-26 (v2 — replaces the June chat-only version)
**Code:** `ai-mastery-dev/02-config-review/` (`config_review.py` baseline · `config_review_rag.py` RAG)
**Status:** ✅ Working code · tested end-to-end on Streamlit Cloud (12 Oct 2026) · part of the "Dinoerla NetOps" dashboard

> **What changed from v1:** v1 (June) was a prompt pasted into a chat. Its regulation references
> ("POJK 11/2022 Pasal X") came from the model's memory and were never verified. v2 is code:
> it **retrieves passages from the actual POJK/SEOJK PDFs** and must cite them. Anything not
> supported by the retrieved text is marked **"(verify)"**. Bank and device names are fictional.

---

## The Problem

**Situation:** PT Bank Arunika (fictional) prepares for an OJK (Otoritas Jasa Keuangan) IT audit.
The CISO must review the hardening of hundreds of routers, switches and firewalls.

**Pain points from the field:**
- Manual config review is slow and depends on which engineer does it
- Regulation is spread across POJK 11/POJK.03/2022 and SEOJK 29/SEOJK.03/2022 — hard to map to config lines
- Generic AI makes it worse in one specific way: it **invents article numbers** with confidence.
  In a compliance report, a wrong citation is worse than no citation.

---

## The Scenario

Sample branch router config (`data/router_sample.cfg`, synthetic):

```
hostname BR-JKT-03
enable password cisco123          ← weak, unencrypted
no service password-encryption
username admin password 0 admin123
ip http server                    ← unencrypted management
snmp-server community public RO   ← default communities, RW access
snmp-server community private RW
line vty 0 4
 transport input telnet           ← cleartext remote access
```

Ground truth (visible in the config itself): weak/plaintext credentials, Telnet, HTTP management,
default SNMP communities with RW, no central logging host.

---

## The Approach — two versions side by side

| | Baseline `config_review.py` | RAG `config_review_rag.py` |
|---|---|---|
| Knowledge source | Model memory + best practice | **Retrieved text from 5 OJK PDFs** (ChromaDB, 280 chunks, shared with CS-105) |
| Regulation claims | Only general areas; any article number → "(verify)" | Each finding has a **DASAR** field citing the retrieved source |
| Retrieval | — | Fixed compliance query → top-4 chunks (`TOP_K = 4`) |
| Output | Finding · Severity · Why risky · Recommendation · Compliance area | Same + **DASAR** (source) + summary per severity + top-3 priorities |
| Mode | Report-only | Report-only |

**Flow (RAG):**
```
config → embed fixed compliance query → ChromaDB top-4 OJK chunks
       → prompt = [regulation context] + [config] → Gemini
       → findings with DASAR (cited) or "(verify)" (best practice only)
```

**Division of labour:** CODE retrieves the regulation and assembles the evidence; **AI** reasons over
config vs regulation; **the engineer** validates severity and context (exceptions, ISP contracts).

---

## What the Domain Expert Still Adds (carried over from v1, still true)

| Capability | AI | Domain expert |
|---|---|---|
| Scan config, flag missing hardening | ✅ seconds | validates |
| Map finding to regulation | ✅ only from retrieved text | checks the cited passage |
| Context ("ISP won't do BGP MD5 — put it in the contract") | ❌ | ✅ |
| Logic errors across lines (v1: `ip default-gateway` on an L3 switch) | ❌ missed in v1 | ✅ |
| Storytelling for the CISO ("unknown device on core-banking VLAN") | flags | frames as audit moment |

---

## Business Value — hypotheses to measure in a pilot (not claims)

| Metric | How to measure |
|---|---|
| Review time per device | Engineer time with vs without the tool, same device set |
| Citation accuracy | % of DASAR citations that an auditor confirms against the PDF |
| Coverage | % of a standard hardening checklist the review flags |
| Consistency | Same config, different engineers → same findings? |

> v1 claimed "~800× faster". That number came from a chat estimate, not a measurement. Removed.

---

## Honest Limitations (and next steps)

1. **Retrieval uses a fixed topic query**, not the config itself — the same 4 chunks come back for every device.
   Next: build the query from the findings (e.g. "Telnet", "SNMP community") so citations get more specific.
2. Chunks are fixed-size (1,200 chars), not per article — a citation points to a document + chunk, not a clean "Pasal X ayat Y".
3. Article-level answers must still be checked against the original PDF before going into an audit report.
4. Synthetic config only. Real client configs must be **masked** before they touch any LLM.

---

## Demo Script (interview / client meeting)

*"Generic AI is dangerous in compliance work because it invents article numbers with confidence.
So I built it differently: the tool first retrieves passages from the actual POJK 11/2022 and SEOJK 29/2022 PDFs,
and every finding must cite one of them. If it can't, it has to say 'verify'.*

*Here's a branch router: Telnet, default SNMP communities with write access, plaintext passwords.
Each finding comes back with severity, a fix, and the regulation passage it's based on.
The engineer's job changes from writing the report to checking the evidence."*

---

## Files

- Code: `02-config-review/` · shared vector DB: `04-ojk-rag/chroma_db`
- Related: CS-105 (OJK RAG Q&A — same knowledge base)
- Previous version: `CS-102-config-review-ojk.md` (June, chat-only — archive)

*AI Mastery Program · Dili Noerlan · v2 2026-10-26*
