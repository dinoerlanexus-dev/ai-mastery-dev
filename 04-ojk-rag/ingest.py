"""
ingest.py - FASE INDEXING RAG
Baca PDF -> chunk -> embed (Gemini) -> simpan ke ChromaDB.
SKIP chunk yang udah ada -> re-run murah (nggak embed ulang). Hemat token.
"""
import os, sys, time, glob
from pypdf import PdfReader
from google import genai
from google.genai import errors
import chromadb

EMBED_MODEL = "gemini-embedding-001"
CHUNK_SIZE  = 1200
OVERLAP     = 200
DOCS_DIR    = "docs"
DB_DIR      = "chroma_db"
COLLECTION  = "ojk"

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("set dulu: export GEMINI_API_KEY='...'")
client = genai.Client(api_key=api_key)

def read_pdf(path):
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    text = " ".join(text.split())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i+size]); i += size - overlap
    return out

def embed(text, retries=3):
    for a in range(1, retries+1):
        try:
            return client.models.embed_content(model=EMBED_MODEL, contents=text).embeddings[0].values
        except errors.ServerError as e:
            if a < retries: print(f"  [retry] server sibuk ({e.code})..."); time.sleep(5*a)
            else: raise

def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(DOCS_DIR, "*.pdf")))
    files = [f if os.path.dirname(f) else os.path.join(DOCS_DIR, f) for f in files]
    if not files:
        print("Nggak ada PDF di docs/"); return

    chroma = chromadb.PersistentClient(path=DB_DIR)
    col = chroma.get_or_create_collection(COLLECTION)
    existing = set(col.get()["ids"])          # id yang SUDAH ada -> di-skip
    print(f"Chunk existing di DB: {len(existing)}\n")

    print("Test embedding..."); print(f"OK - dim: {len(embed('uji coba'))}\n")

    baru, skip = 0, 0
    for path in files:
        name = os.path.basename(path)
        chunks = chunk_text(read_pdf(path))
        print(f"[{name}] {len(chunks)} chunk...")
        for j, ch in enumerate(chunks):
            cid = f"{name}::{j}"
            if cid in existing:               # SKIP: udah di-embed
                skip += 1; continue
            col.upsert(ids=[cid], embeddings=[embed(ch)], documents=[ch],
                       metadatas=[{"source": name, "chunk": j}])
            baru += 1
            if baru % 10 == 0: print(f"    +{baru} baru")
            time.sleep(0.3)
    print(f"\n=== SELESAI. Baru di-embed: {baru} | Skip (udah ada): {skip} | Total DB: {col.count()} ===")

if __name__ == "__main__":
    main()
