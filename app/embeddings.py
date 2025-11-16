import os
import json
import math
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

# Chunking config
CHUNK_SIZE_WORDS = 150
CHUNK_OVERLAP = 30

EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")

def chunk_text(text: str, chunk_size=CHUNK_SIZE_WORDS, overlap=CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        j = min(i + chunk_size, n)
        chunk = " ".join(words[i:j])
        chunks.append(chunk)
        if j == n:
            break
        i = j - overlap
    return chunks

class Embedder:
    def __init__(self, model_name=EMBED_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        arr = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        # normalize for cosine search
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms
        return arr

def build_faiss_index(vectors: np.ndarray) -> faiss.Index:
    dim = vectors.shape[1]
    # IndexFlatIP expects vectors normalized for cosine (dot-product ~ cosine)
    index = faiss.IndexFlatIP(dim)
    index.add(vectors.astype('float32'))
    return index

def save_index(index: faiss.Index, metadata: List[Dict], out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(Path(out_dir) / "faiss.index"))
    with open(Path(out_dir) / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def load_index(out_dir: str) -> Tuple[faiss.Index, List[Dict]]:
    idx_path = Path(out_dir) / "faiss.index"
    meta_path = Path(out_dir) / "metadata.json"
    if not idx_path.exists() or not meta_path.exists():
        raise FileNotFoundError("Index or metadata not found in " + out_dir)
    index = faiss.read_index(str(idx_path))
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return index, metadata

def build_index_from_documents(docs: List[Dict], embedder: Embedder = None) -> Tuple[faiss.Index, List[Dict]]:
    """
    docs: list of dicts with keys: 'id', 'text', 'source' (optional), 'section' (optional)
    returns: faiss index and metadata list aligned with index ids
    """
    if embedder is None:
        embedder = Embedder()
    all_chunks = []
    metadatas = []
    for doc in docs:
        text = doc.get("text", "")
        chunks = chunk_text(text)
        for i, ch in enumerate(chunks):
            meta = {
                "doc_id": doc.get("id"),
                "source": doc.get("source"),
                "section": doc.get("section"),
                "chunk_index": i,
                "chunk_text_preview": ch[:300]
            }
            all_chunks.append(ch)
            metadatas.append(meta)
    if not all_chunks:
        raise ValueError("No chunks to index")
    vecs = embedder.encode(all_chunks)
    index = build_faiss_index(vecs)
    return index, metadatas

if __name__ == "__main__":
    # small smoke test
    docs = [
        {"id": "r1", "text": "Experienced data scientist with Python, SQL and Pandas. Worked on ETL and analytics."},
        {"id": "j1", "text": "We need a Python developer with expertise in SQL and data analytics. Familiarity with Pandas is a plus."}
    ]
    emb = Embedder()
    idx, metas = build_index_from_documents(docs, emb)
    print("Index size:", idx.ntotal)
    # query
    q = "Python SQL analytics"
    qv = emb.encode([q])
    D, I = idx.search(qv.astype('float32'), k=3)
    print("Distances:", D)
    print("Indices:", I)
    for idxi in I[0]:
        if idxi < len(metas):
            print(metas[idxi])
