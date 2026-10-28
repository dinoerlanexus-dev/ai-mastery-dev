# CS-105 — OJK Regulation Q&A with RAG: Answers That Cite the Source, or Say "Not Found"
**Category:** AI Usecase · Compliance · Working code
**Date:** 2026-10-26
**Code:** `ai-mastery-dev/04-ojk-rag/` (`ingest.py`, `ask_ojk.py`, `chroma_db/`)
**Status:** ✅ Working code · tested on Streamlit Cloud (12 Oct 2026) · knowledge base reused by CS-102 v2

---

## The Problem

**Situation:** Network, security and IT-risk teams at PT Bank Arunika (fictional) constantly ask
"what does OJK actually require for X?" — data-centre placement, DRC (Disaster Recovery Center),
cyber resilience, outsourcing.

**Pain points from the field:**
- The answers live in long PDFs (POJK 11/2022, SEOJK 29/2022, FAQs, summaries)
- Asking a generic chatbot is dangerous: it answers fluently **from memory** and may invent
  article numbers — unacceptable for compliance
- Compliance teams need the **source**, not just the answer

---

## What RAG Is (one line)

**RAG (Retrieval-Augmented Generation)** = before the AI answers, code searches the real documents
and gives the AI only the relevant passages. The AI must answer from those passages.

Analogy: an engineer who answers "per the design document, section 4.2…" versus one who answers from memory.

---

## The Build

| Phase | Script | What it does |
|---|---|---|
| **Indexing** (once) | `ingest.py` | Read 5 PDFs → split into 1,200-character chunks (200 overlap) → embed with `gemini-embedding-001` → store in **ChromaDB** (local vector DB). Re-runs skip chunks already stored. |
| **Query** (every question) | `ask_ojk.py` | Embed the question → retrieve top-5 most similar chunks → prompt Gemini with those chunks only → answer + source names |

**Knowledge base:** 5 public OJK documents → **280 chunks**
- POJK 11/POJK.03/2022 (IT governance for commercial banks) + its FAQ and summary
- SEOJK 29/SEOJK.03/2022 (cyber security & resilience) + summary

**Honesty guard in the prompt:**
- Answer only from the context
- If the answer is not in the context, say exactly: *"Tidak ditemukan di dokumen yang tersedia."*
- Never invent articles; name the source document for every point

---

## Test Results (Streamlit Cloud, 12 Oct 2026)

| Question | Result |
|---|---|
| Data-centre / DRC placement requirements | ✅ Answer with source documents cited |
| "Harga bitcoin hari ini?" (off-topic) | ✅ *"Tidak ditemukan di dokumen yang tersedia"* — the AI refused to guess |

---

## What's Good, What's Not (honest)

| ✅ Works | ⚠️ Limitation | Next |
|---|---|---|
| Answers cite the source document | Chunks are fixed-size, not per article → citation = document + chunk, not "Pasal X ayat Y" | Chunk per article |
| Refuses off-topic questions | The refusal comes from the **prompt**. Retrieval still pulls 5 chunks even for "bitcoin" | **Similarity threshold**: below a score, return "not found" before calling AI (defense in depth) |
| Re-runnable ingest (skip existing) | An answer quoting "Pasal 41 ayat 1–2" still needs checking against the PDF | Human verification before any audit use |
| Shared knowledge base (CS-102 v2 reuses it) | Data leaves the bank to a public API | Production: Vertex AI in an approved region (verify availability), no API key, audit logs |

---

## Business Value — hypotheses to measure in a pilot

| Metric | How to measure |
|---|---|
| Time to answer a regulation question | Minutes with tool vs manual PDF search |
| Citation accuracy | % of answers whose cited passage really supports the answer (auditor review) |
| Hallucination rate | % of off-topic / unanswerable questions correctly refused |

---

## Demo Script (interview / client meeting)

*"The biggest risk of AI in compliance is a confident wrong answer. So this tool doesn't answer from memory.
It first searches the actual POJK and SEOJK documents, gives the AI only those passages,
and the AI must name its source.*

*Watch — I ask about DRC placement: answer plus the documents it came from.
Now I ask the price of bitcoin: 'not found in the available documents.' That refusal is the feature.
For a bank, an AI that knows what it doesn't know is worth more than one that always has an answer."*

---

## Files

- Code: `04-ojk-rag/` · documents: `docs/` · vector DB: `chroma_db/`
- Screenshots: `04-ojk-rag/deliverables/` (one OJK question, one off-topic question)
- Related: CS-102 v2 (config review grounded in the same knowledge base)

*AI Mastery Program · Dili Noerlan · 2026-10-26*
