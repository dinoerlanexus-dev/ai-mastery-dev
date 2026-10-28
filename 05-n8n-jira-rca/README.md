# 05 — AI RCA inside the ticket flow (n8n + Jira Service Management)

**AI drafts. A human verifies. Automation publishes.** The NOC already lives in its ticketing tool, so the AI
lives there too — no separate chatbot.

## Flow — three workflows, one state machine in the ticket label

```
Engineer adds label  ai-rca
        │
WF-1  (poll every 5 min) → keep 3 fields → Gemini RCA draft
        → INTERNAL note (customers can't see it) → label ai-rca-draft
        │
Engineer reviews, writes the verified cause as an internal note,
changes label → ai-rca-verified                       ← human gate, AI never sets this
        │
WF-2  (poll every 5 min) → read all comments, tag [AI DRAFT] / [ENGINEER]
        → Gemini executive summary in Bahasa Indonesia ([ENGINEER] overrides AI)
        → INTERNAL note "RINGKASAN EKSEKUTIF – FINAL" → label ai-rca-final

WF-0  any failure in WF-1 / WF-2 → email: workflow, node, error, link to the failed run
```

## Design choices
| Choice | Why |
|---|---|
| Label = state; workflows never call each other | Each can fail without breaking the other; a failed ticket simply stays queued |
| Polling, not webhook | Lab runs behind NAT |
| Only summary + description reach the AI | Less data exposure — the natural masking point |
| Internal note (`sd.public.comment` → `internal: true`) via Jira REST API v2 | AI drafts are never customer-visible |
| Label changes only after the note is posted | No "done" state on a failed run |
| Retry 3× on the AI node + error workflow | The AI API returned 503 several times during testing — alert fired, ticket processed after recovery |

## Files
| File | Workflow |
|---|---|
| `wf-0-error-notifier.json` | Error Trigger → email (SMTP) |
| `wf-1-rca-v1.1.json` | Schedule → Jira search → Edit Fields → Gemini → internal note → label |
| `wf-2-exec-summary.json` | Schedule → Jira search → get comments → Edit Fields → Gemini → internal note → label |
| `workflow-v1.json` | First version (public comment), kept for reference |

## Import
1. n8n → *Import from file* for each JSON. Import WF-0 first and **publish** it, then select it as the *Error workflow* in WF-1 and WF-2 settings.
2. Create your own credentials (Jira Cloud API token, Gemini API key, SMTP) — the exports contain credential **names only**, no secrets.
3. Replace the placeholders `YOUR-SITE.atlassian.net` (HTTP nodes) and `you@example.com` (WF-0).
4. Create the labels `ai-rca`, `ai-rca-draft`, `ai-rca-verified`, `ai-rca-final` on any ticket so they appear in Jira.
5. Set the workflow timezone, then publish.

## Tested on purpose
- JQL syntax error → alert email within a minute, link opens the failed run.
- JQL for a non-existent project → Jira returns 0 tickets **without an error** → silent failure; a heartbeat is on the backlog.
- Real AI 503 → retries exhausted → alert → ticket stayed queued → processed automatically after recovery.

## Backlog
Fallback model on 503 · one alert per incident (rate-limit) · heartbeat · ranked hypotheses in the draft ·
dedicated bot account for a clean audit trail · production hosting (Docker / managed n8n).

## Screenshots

![AI RCA draft as an internal note](../docs/images/jira-ai-rca-draft.png)
![Executive summary built from the engineer's verified cause](../docs/images/jira-exec-summary-final.png)
![WF-2 production run, 7 nodes, 42 s](../docs/images/n8n-wf2-production-run.png)

Case study: [CS-106](../docs/case-studies/CS-106-n8n-jira-ai-rca.md)
