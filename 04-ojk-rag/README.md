# 04 — OJK RAG (compliance grounding)

Tujuan: AI menjawab/mengecek compliance berdasarkan TEKS REGULASI ASLI (bukan tebakan
training). RAG = Retrieval Augmented Generation.

## STATUS: menunggu dokumen (belum dibangun)

## Dokumen yang perlu di-download (dari ojk.go.id) -> taruh di folder docs/
1. POJK No. 11/POJK.03/2022 - Penyelenggaraan Teknologi Informasi oleh Bank Umum
2. SEOJK No. 29/SEOJK.03/2022 - Ketahanan dan Keamanan Siber bagi Bank Umum
(opsional nanti: regulasi lain yang relevan, mis. terkait sistem pembayaran / BI-FAST)

Simpan sebagai PDF asli di: 04-ojk-rag/docs/

## Rencana build (sesi berikutnya) - konsep baru
1. Load PDF -> ekstrak teks
2. Chunk: potong teks jadi bagian kecil (mis. per pasal/paragraf)
3. Embedding: ubah tiap chunk jadi vektor (pakai Gemini embeddings, free tier)
4. Vector store: simpan di ChromaDB (lokal)
5. Query: pertanyaan -> cari chunk paling relevan -> kasih ke AI sbagai konteks
   -> AI jawab + KUTIP pasal yang beneran ada (grounded, bukan ngarang)

## Kaitan
- Upgrade usecase 02 (config-review) & 03 (sla) supaya cite pasal OJK asli.
