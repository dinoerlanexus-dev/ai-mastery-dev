"""
test_ojk_rag.py - Smoke test usecase 04-ojk-rag.

- ingest.py : chunk_text (real, deterministic), read_pdf (real, PDF OJK di docs/),
              logic SKIP chunk existing (hemat token) pakai FAKE Chroma + MOCK embed.
- ask_ojk.py: wiring question -> embed -> retrieve -> prompt -> AI, pakai FAKE Chroma + MOCK.
- Guardrail : "Tidak ditemukan di dokumen yang tersedia." wajib ada di prompt (anti-halusinasi).
chroma_db/ di-gitignore -> CI gak punya DB -> semua akses Chroma di-fake.

Jalanin: cd "04-ojk-rag" && pytest test_ojk_rag.py -v
"""
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _m in ("ingest", "ask_ojk"):
    sys.modules.pop(_m, None)

# Script asli (versi lo, gak diubah) langsung STOP kalau GEMINI_API_KEY kosong.
# Jadi test pasang key PALSU dulu sebelum import. Semua panggilan AI di-mock,
# jadi key palsu ini gak pernah dipake ke Gemini (nol token, nol biaya).
os.environ["GEMINI_API_KEY"] = "dummy-key-test-only"

import ingest
import ask_ojk


# ---------- chunk_text (real) ----------

def test_chunk_empty_text():
    assert ingest.chunk_text("") == []


def test_chunk_normalizes_whitespace():
    assert ingest.chunk_text("Pasal   1\n\n ayat\t(2)") == ["Pasal 1 ayat (2)"]


def test_chunk_size_and_overlap():
    text = "".join(chr(65 + (i % 26)) for i in range(3000))   # 3000 char tanpa spasi
    chunks = ingest.chunk_text(text, size=1200, overlap=200)
    assert len(chunks) == 3                       # start 0, 1000, 2000
    assert all(len(c) <= 1200 for c in chunks)
    assert chunks[0][-200:] == chunks[1][:200]    # overlap 200 char nyambung
    assert chunks[2] == text[2000:]


# ---------- read_pdf (real, dokumen OJK di repo) ----------

def test_read_pdf_extracts_text_from_ojk_doc():
    text = ingest.read_pdf(os.path.join(HERE, "docs", "RINGKASAN POJK 11 - 03 - 2022.pdf"))
    assert len(text) > 500          # bukan PDF hasil scan kosong
    assert "POJK" in text


# ---------- fake Chroma ----------

class FakeCollection:
    def __init__(self, existing_ids=()):
        self.existing = list(existing_ids)
        self.upserts = []
        self.query_args = None

    def get(self):
        return {"ids": self.existing}

    def upsert(self, ids, embeddings, documents, metadatas):
        self.upserts.append((ids[0], metadatas[0]))

    def count(self):
        return len(self.existing) + len(self.upserts)

    def query(self, query_embeddings, n_results):
        self.query_args = (query_embeddings, n_results)
        return {"documents": [["Bank wajib memiliki rencana pemulihan bencana."]],
                "metadatas": [[{"source": "POJK 11 - 03 - 2022.pdf", "chunk": 42}]]}


def fake_chroma_factory(col):
    return lambda path: types.SimpleNamespace(get_or_create_collection=lambda name: col)


# ---------- ingest: skip logic (hemat token) ----------

def test_ingest_skips_existing_chunks(monkeypatch, capsys):
    col = FakeCollection(existing_ids=["x.pdf::0"])
    embedded = []
    monkeypatch.setattr(ingest.chromadb, "PersistentClient", fake_chroma_factory(col))
    monkeypatch.setattr(ingest, "read_pdf", lambda path: "A" * 2500)   # -> 3 chunk
    monkeypatch.setattr(ingest, "embed", lambda t: embedded.append(t) or [0.1])
    monkeypatch.setattr(ingest.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["ingest.py", "x.pdf"])

    ingest.main()

    assert [cid for cid, _ in col.upserts] == ["x.pdf::1", "x.pdf::2"]   # ::0 di-skip
    assert len(embedded) == 1 + 2        # 1x test embedding + 2 chunk baru
    assert "Skip (udah ada): 1" in capsys.readouterr().out


# ---------- ask_ojk: wiring ----------

def test_ask_ojk_wiring(monkeypatch, capsys):
    col = FakeCollection()
    seen = {"embed": [], "prompt": None}
    monkeypatch.setattr(ask_ojk.chromadb, "PersistentClient", fake_chroma_factory(col))
    monkeypatch.setattr(ask_ojk, "embed", lambda t: seen["embed"].append(t) or [0.1])
    monkeypatch.setattr(ask_ojk, "ask_ai", lambda p: seen.__setitem__("prompt", p) or "MOCK JAWABAN")
    monkeypatch.setattr(sys, "argv", ["ask_ojk.py", "apa", "kewajiban", "DRC?"])

    ask_ojk.main()

    assert seen["embed"] == ["apa kewajiban DRC?"]          # yang di-embed = pertanyaan
    assert col.query_args[1] == ask_ojk.TOP_K
    assert "[Sumber: POJK 11 - 03 - 2022.pdf]" in seen["prompt"]
    assert "PERTANYAAN: apa kewajiban DRC?" in seen["prompt"]
    assert "{context}" not in seen["prompt"] and "{question}" not in seen["prompt"]
    out = capsys.readouterr().out
    assert "POJK 11 - 03 - 2022.pdf (chunk 42)" in out
    assert "MOCK JAWABAN" in out


def test_ask_ojk_no_question_no_api_call(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(ask_ojk, "embed", lambda t: called.append(t))
    monkeypatch.setattr(sys, "argv", ["ask_ojk.py"])
    ask_ojk.main()
    assert called == []
    assert "Pakai:" in capsys.readouterr().out


def test_prompt_guardrail_not_found_answer():
    assert "Tidak ditemukan di dokumen yang tersedia." in ask_ojk.PROMPT
    assert "JANGAN mengarang pasal" in ask_ojk.PROMPT
