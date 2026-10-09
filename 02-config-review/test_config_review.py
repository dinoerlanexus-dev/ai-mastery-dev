"""
test_config_review.py - Smoke test usecase 02-config-review (pola sama kayak 01-network-rca).

- config_review.py     : prompt library + wiring run_check -> ask_ai (MOCK, no API).
- config_review_rag.py : wiring RAG retrieve -> prompt -> AI, pakai FAKE ChromaDB + MOCK
                         embed/ask_ai. Jadi CI gak butuh chroma_db/ (gitignored) & gak butuh key.
- Guardrail test: pastiin aturan anti-halusinasi regulasi di prompt gak ke-hapus diam-diam.

Jalanin: cd "02-config-review" && pytest test_config_review.py -v
"""
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# 01/02/03 sama-sama punya prompts.py -> buang cache biar yang ke-import punya folder INI
for _m in ("prompts", "config_review", "config_review_rag"):
    sys.modules.pop(_m, None)

# Script asli (versi lo, gak diubah) langsung STOP kalau GEMINI_API_KEY kosong.
# Jadi test pasang key PALSU dulu sebelum import. Semua panggilan AI di-mock,
# jadi key palsu ini gak pernah dipake ke Gemini (nol token, nol biaya).
os.environ["GEMINI_API_KEY"] = "dummy-key-test-only"

import prompts
import config_review
import config_review_rag

SAMPLE = open(os.path.join(HERE, "data", "router_sample.cfg")).read()


# ---------- config_review.py (non-RAG) ----------

def test_prompt_library_has_config_review_with_placeholder():
    assert "config_review" in prompts.PROMPTS
    assert "{data}" in prompts.PROMPTS["config_review"]


def test_prompt_guardrails_present():
    p = prompts.PROMPTS["config_review"]
    assert "REPORT-ONLY" in p
    assert "JANGAN mengarang nomor pasal" in p
    assert "(verify)" in p


def test_unknown_check_rejected_before_api(monkeypatch):
    called = []
    monkeypatch.setattr(config_review, "ask_ai", lambda p: called.append(p))
    out = config_review.run_check("check_ngawur", SAMPLE)
    assert "nggak ada" in out
    assert called == []          # gak buang token buat check yang gak ada


def test_run_check_builds_prompt_with_config(monkeypatch):
    captured = {}

    def fake_ask(p):
        captured["prompt"] = p
        return "MOCK REVIEW"

    monkeypatch.setattr(config_review, "ask_ai", fake_ask)
    assert config_review.run_check("config_review", SAMPLE) == "MOCK REVIEW"
    assert "enable password cisco123" in captured["prompt"]   # config beneran masuk
    assert "{data}" not in captured["prompt"]                 # placeholder ke-replace


# ---------- config_review_rag.py (RAG, fake Chroma) ----------

class FakeCollection:
    def __init__(self):
        self.query_args = None

    def query(self, query_embeddings, n_results):
        self.query_args = (query_embeddings, n_results)
        return {
            "documents": [["Isi pasal A tentang autentikasi", "Isi pasal B tentang audit trail"]],
            "metadatas": [[{"source": "POJK 11.pdf", "chunk": 3},
                           {"source": "SEOJK 29.pdf", "chunk": 7}]],
        }


@pytest.fixture
def rag(monkeypatch):
    col = FakeCollection()
    seen = {"embed": [], "prompt": None, "path": None, "name": None}

    def fake_client(path):
        seen["path"] = path

        def get_col(name):
            seen["name"] = name
            return col
        return types.SimpleNamespace(get_or_create_collection=get_col)

    def fake_embed(text):
        seen["embed"].append(text)
        return [0.1, 0.2, 0.3]

    def fake_ask(p):
        seen["prompt"] = p
        return "MOCK GROUNDED REVIEW"

    monkeypatch.setattr(config_review_rag.chromadb, "PersistentClient", fake_client)
    monkeypatch.setattr(config_review_rag, "embed", fake_embed)
    monkeypatch.setattr(config_review_rag, "ask_ai", fake_ask)
    return col, seen


def test_rag_uses_shared_ojk_db(rag):
    col, seen = rag
    config_review_rag.review_config(SAMPLE)
    assert os.path.normpath(seen["path"]).endswith(os.path.join("04-ojk-rag", "chroma_db"))
    assert seen["name"] == "ojk"


def test_rag_retrieves_by_compliance_topic_not_raw_config(rag):
    col, seen = rag
    config_review_rag.review_config(SAMPLE)
    assert seen["embed"] == [config_review_rag.RETRIEVE_QUERY]   # 1x embed, query topik
    assert col.query_args[1] == config_review_rag.TOP_K


def test_rag_prompt_contains_sources_context_and_config(rag):
    col, seen = rag
    out = config_review_rag.review_config(SAMPLE)
    p = seen["prompt"]
    assert "[Sumber: POJK 11.pdf]" in p and "[Sumber: SEOJK 29.pdf]" in p
    assert "Isi pasal A tentang autentikasi" in p
    assert "snmp-server community public RO" in p
    assert "{context}" not in p and "{config}" not in p
    assert out["result"] == "MOCK GROUNDED REVIEW"
    assert [m["source"] for m in out["sources"]] == ["POJK 11.pdf", "SEOJK 29.pdf"]


def test_rag_prompt_guardrail_present():
    assert "JANGAN mengarang pasal di luar KONTEKS" in config_review_rag.PROMPT
    assert "(verify)" in config_review_rag.PROMPT


def test_rag_embed_and_ask_without_key_raise(monkeypatch):
    monkeypatch.setattr(config_review_rag, "client", None)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        config_review_rag.embed("x")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        config_review_rag.ask_ai("x")
