"""peek.py - intip isi ChromaDB (nggak butuh internet, cuma baca lokal)."""
import chromadb
col = chromadb.PersistentClient(path="chroma_db").get_or_create_collection("ojk")
print("Total chunk tersimpan:", col.count(), "\n")
res = col.get(limit=2, include=["documents", "metadatas"])
for doc, meta in zip(res["documents"], res["metadatas"]):
    print(f"--- {meta['source']} (chunk {meta['chunk']}) ---")
    print(doc[:650], "...\n")
