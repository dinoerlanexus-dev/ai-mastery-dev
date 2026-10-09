"""
config_review_rag.py - USECASE #2 versi RAG
Review config vs best-practice + KUTIP pasal OJK asli (grounded).
Reuse ChromaDB dari 04-ojk-rag (nggak embed ulang).
Pakai: python config_review_rag.py [file_config]
"""
import os, sys, time
from google import genai
from google.genai import errors
import chromadb

EMBED_MODEL = "gemini-embedding-001"
CHAT_MODEL  = "gemini-3.6-flash"
TOP_K       = 4          # jumlah pasal OJK yang di-retrieve (kecil = hemat token)

# Path ke ChromaDB SHARED di 04-ojk-rag (relatif ke lokasi file ini)
BASE   = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE, "..", "04-ojk-rag", "chroma_db")
COLLECTION = "ojk"

# Query topik compliance buat narik pasal relevan (bukan config mentah)
RETRIEVE_QUERY = ("kewajiban keamanan dan ketahanan siber, akses kontrol, autentikasi, "
                  "enkripsi, logging dan audit trail, manajemen risiko teknologi informasi bank")

api_key = os.environ.get("GEMINI_API_KEY")
# Lazy init - sama pola kayak 01-network-rca/engine.py: jangan crash pas di-import
# (misal dari dashboard_app.py gabungan), error jelas baru muncul pas beneran dipanggil.
client = genai.Client(api_key=api_key) if api_key else None

def embed(text, retries=3):
    if client is None:
        raise RuntimeError("GEMINI_API_KEY belum di-set. Jalankan: export GEMINI_API_KEY='...'")
    for a in range(1, retries+1):
        try:
            return client.models.embed_content(model=EMBED_MODEL, contents=text).embeddings[0].values
        except errors.ServerError:
            if a < retries: time.sleep(5*a)
            else: raise

def ask_ai(prompt, retries=3):
    if client is None:
        raise RuntimeError("GEMINI_API_KEY belum di-set. Jalankan: export GEMINI_API_KEY='...'")
    for a in range(1, retries+1):
        try:
            return client.models.generate_content(model=CHAT_MODEL, contents=prompt).text
        except errors.ServerError as e:
            if a < retries: print(f"[retry] server sibuk ({e.code})..."); time.sleep(5*a)
            else: raise

PROMPT = """Kamu security & compliance reviewer jaringan bank Indonesia.
Di bawah ada (A) KONTEKS REGULASI (kutipan POJK/SEOJK asli hasil retrieve) dan (B) CONFIG device.

Review CONFIG terhadap best-practice keamanan DAN terhadap KONTEKS regulasi.
Format tiap temuan:
- TEMUAN
- SEVERITY (High/Medium/Low)
- KENAPA BERISIKO
- REKOMENDASI (command kalau relevan)
- DASAR: kalau didukung KONTEKS, kutip sumbernya. Kalau cuma best-practice umum (nggak ada di KONTEKS), tandai "(verify)".

ATURAN: REPORT-ONLY. JANGAN mengarang pasal di luar KONTEKS. Akhiri dengan ringkasan per severity + 3 prioritas.

=== (A) KONTEKS REGULASI (retrieved) ===
{context}

=== (B) CONFIG ===
{config}
"""

def review_config(config_text: str) -> dict:
    """
    Fungsi inti, reusable - dipanggil CLI (main() di bawah) MAUPUN dashboard.
    Retrieve pasal OJK relevan dari ChromaDB, lalu AI review config terhadap itu.
    Return dict: {"sources": [...metadata chunk...], "context": "...", "result": "..."}
    """
    col = chromadb.PersistentClient(path=DB_DIR).get_or_create_collection(COLLECTION)
    res = col.query(query_embeddings=[embed(RETRIEVE_QUERY)], n_results=TOP_K)
    docs, metas = res["documents"][0], res["metadatas"][0]
    context = "\n\n---\n\n".join(f"[Sumber: {m['source']}]\n{d}" for d, m in zip(docs, metas))
    result = ask_ai(PROMPT.replace("{context}", context).replace("{config}", config_text))
    return {"sources": metas, "context": context, "result": result}


def main():
    datafile = sys.argv[1] if len(sys.argv) > 1 else "data/router_sample.cfg"
    with open(datafile) as f:
        config = f.read()

    print(f"Config: {datafile}")
    out = review_config(config)
    print("Pasal OJK yang di-retrieve (grounding):")
    for m in out["sources"]: print(f"  - {m['source']} (chunk {m['chunk']})")
    print("\n=== REVIEW (grounded ke OJK) ===")
    print(out["result"])

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"File nggak ketemu: {e}")
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except RuntimeError as e:
        print(f"CONFIG ERROR: {e}")
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
