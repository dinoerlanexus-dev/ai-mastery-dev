# 02 — Config Review (AI-assisted)

Fungsi: baca config device -> AI review vs best-practice + regulasi OJK -> report gap.
REPORT-ONLY (tidak mengubah config).

Dua versi:
1. **config_review.py** — baseline. Best-practice keamanan + prinsip umum OJK/PBI,
   TIDAK grounded ke teks regulasi asli. Klaim soal pasal spesifik selalu ditandai "(verify)".
2. **config_review_rag.py** — versi RAG (grounded). Retrieve pasal OJK/SEOJK asli dari
   ChromaDB shared di `04-ojk-rag` (280 chunk, TOP_K=4), kutip sumber per temuan lewat
   field DASAR. Guard "(verify)" tetap dipakai buat temuan yang nggak didukung konteks
   retrieved (murni best-practice umum).

## Dependency (buat versi RAG)
`config_review_rag.py` reuse ChromaDB dari `../04-ojk-rag/chroma_db` — TIDAK embed ulang.
Kalau folder itu belum ke-ingest, jalanin dulu `ingest.py` di `04-ojk-rag`.

## Cara jalanin
1) Setup dulu dari folder induk (lihat README induk): activate venv + export key.
2) Masuk folder ini & jalanin salah satu:

    cd 02-config-review

    # baseline (non-RAG)
    python config_review.py                          # default: data/router_sample.cfg
    python config_review.py config_review data/router_sample.cfg   # bentuk eksplisit

    # RAG (grounded ke pasal OJK asli)
    python config_review_rag.py                       # default: data/router_sample.cfg
    python config_review_rag.py data/config_lo.cfg     # ganti input

## Isi folder
- config_review.py     -> baseline, non-RAG.
- config_review_rag.py -> versi RAG, grounded ke pasal OJK asli via ChromaDB shared.
- prompts.py            -> prompt review buat versi baseline (best-practice + OJK umum, report-only, guard "(verify)").
- data/                 -> config contoh: router_sample.cfg.
