from typing import List, Tuple, Dict
import numpy as np
from app.embeddings import Embedder, load_index
import faiss

def retrieve(query: str, index: faiss.Index, metadata: List[Dict], top_k: int = 5, embedder: Embedder = None):
    if embedder is None:
        embedder = Embedder()
    qv = embedder.encode([query]).astype('float32')
    D, I = index.search(qv, k=top_k)
    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0:
            continue
        meta = metadata[idx] if idx < len(metadata) else {}
        results.append({
            "score": float(score),
            "metadata": meta
        })
    return results

if __name__ == "__main__":
    # example usage
    from app.embeddings import Embedder, build_index_from_documents
    docs = [
        {"id": "r1", "text": "Experienced data scientist with Python, SQL and Pandas. Worked on ETL and analytics."},
        {"id": "j1", "text": "We need a Python developer with expertise in SQL and data analytics. Familiarity with Pandas is a plus."}
    ]
    emb = Embedder()
    idx, metas = build_index_from_documents(docs, emb)
    res = retrieve("python analytics", idx, metas, top_k=3, embedder=emb)
    print(res)
