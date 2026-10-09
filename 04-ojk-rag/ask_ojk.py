"""
ask_ojk.py - FASE QUERY RAG
Pertanyaan -> embed -> cari chunk relevan di ChromaDB -> AI jawab DARI chunk + kutip sumber.
Pakai: python ask_ojk.py "pertanyaan lo"
"""
import os, sys, time
from google import genai
from google.genai import errors
import chromadb

EMBED_MODEL = "gemini-embedding-001"
CHAT_MODEL  = "gemini-3.6-flash"
DB_DIR      = "chroma_db"
COLLECTION  = "ojk"
TOP_K       = 5     # ambil 5 chunk paling relevan

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("set dulu: export GEMINI_API_KEY='...'")
client = genai.Client(api_key=api_key)

def embed(text, retries=3):
    for a in range(1, retries+1):
        try:
            return client.models.embed_content(model=EMBED_MODEL, contents=text).embeddings[0].values
        except errors.ServerError as e:
            if a < retries: time.sleep(5*a)
            else: raise

def ask_ai(prompt, retries=3):
    for a in range(1, retries+1):
        try:
            return client.models.generate_content(model=CHAT_MODEL, contents=prompt).text
        except errors.ServerError as e:
            if a < retries:
                print(f"[retry] server sibuk ({e.code})..."); time.sleep(5*a)
            else: raise

PROMPT = """Kamu asisten kepatuhan regulasi OJK untuk bank di Indonesia.
Jawab pertanyaan HANYA berdasarkan KONTEKS di bawah (kutipan dari dokumen regulasi asli).

ATURAN KERAS:
- Jawab dari konteks. Kalau jawabannya TIDAK ADA di konteks, bilang jujur:
  "Tidak ditemukan di dokumen yang tersedia."
- JANGAN mengarang pasal atau isi yang tidak ada di konteks.
- Sebutkan SUMBER (nama dokumen) yang mendukung tiap poin.

KONTEKS:
{context}

PERTANYAAN: {question}

JAWABAN (ringkas, sebut sumber):"""

def main():
    if len(sys.argv) < 2:
        print('Pakai: python ask_ojk.py "pertanyaan lo"'); return
    question = " ".join(sys.argv[1:])

    col = chromadb.PersistentClient(path=DB_DIR).get_or_create_collection(COLLECTION)

    # 1) embed pertanyaan  2) cari chunk terdekat
    res = col.query(query_embeddings=[embed(question)], n_results=TOP_K)
    docs, metas = res["documents"][0], res["metadatas"][0]

    context = "\n\n---\n\n".join(f"[Sumber: {m['source']}]\n{d}" for d, m in zip(docs, metas))
    prompt = PROMPT.replace("{context}", context).replace("{question}", question)

    print(f"PERTANYAAN: {question}\n")
    print("Chunk yang di-retrieve (bukti grounding):")
    for m in metas:
        print(f"  - {m['source']} (chunk {m['chunk']})")
    print("\n=== JAWABAN (grounded ke dokumen asli) ===")
    print(ask_ai(prompt))

if __name__ == "__main__":
    try:
        main()
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
