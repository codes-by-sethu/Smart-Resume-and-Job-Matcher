from typing import List, Dict, Tuple
import numpy as np
from app.embeddings import Embedder, build_index_from_documents, save_index, load_index
from pathlib import Path
import json

def doc_level_embedding(text: str, embedder: Embedder = None) -> np.ndarray:
    """
    Produce a single vector representing the whole document by encoding either:
    - the whole text, or
    - average of chunk embeddings (we do whole-text encode here for simplicity).
    Returned vector is normalized.
    """
    if embedder is None:
        embedder = Embedder()
    vec = embedder.encode([text])[0]
    # Ensure float32
    return vec.astype('float32')

def build_doc_embeddings(documents: List[Dict], embedder: Embedder = None) -> Tuple[np.ndarray, List[Dict]]:
    """
    documents: list of dicts with keys: id, text, source, parsed (optional)
    returns: (N x D) numpy array of normalized vectors, and metadata list aligned with rows
    """
    if embedder is None:
        embedder = Embedder()
    texts = [d.get("text", "") for d in documents]
    vecs = embedder.encode(texts).astype('float32')
    metas = []
    for d in documents:
        metas.append({
            "id": d.get("id"),
            "source": d.get("source"),
            "parsed": d.get("parsed", {})
        })
    return vecs, metas

def match_resume_to_jobs(resume_vec: np.ndarray, job_vecs: np.ndarray, job_metas: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Cosine similarity (dot product on normalized vectors).
    Handles shape edge cases so result is always a 1-D array of similarities.
    resume_vec: (D,) or (1,D) vector
    job_vecs: (N, D) or (D,) vector (single job)
    """
    import numpy as np

    # Ensure job_vecs is 2-D: (N, D)
    if job_vecs.ndim == 1:
        job_vecs = job_vecs.reshape(1, -1)

    # Ensure resume_vec is 1-D (D,)
    if resume_vec.ndim == 2 and resume_vec.shape[0] == 1:
        resume_vec = resume_vec.reshape(-1)
    elif resume_vec.ndim > 2:
        resume_vec = resume_vec.reshape(-1)

    # Compute dot products -> (N,)
    sims = job_vecs @ resume_vec
    sims = np.asarray(sims).reshape(-1)  # ensure 1-D

    # argsort descending
    idx = np.argsort(-sims)[:top_k]
    results = []
    for i in idx:
        results.append({
            "job_index": int(i),
            "job_id": job_metas[i].get("id"),
            "job_source": job_metas[i].get("source"),
            "score": float(sims[i]),
            "job_meta": job_metas[i]
        })
    return results

if __name__ == "__main__":
    # quick local test using sample docs
    from ingestion.parsers import extract_text, parse_basic_sections
    # sample files (adjust paths)
    files = ["data/sample_resume.pdf", "data/sample_job1.txt", "data/sample_job2.txt"]
    docs = []
    for i, f in enumerate(files):
        txt = extract_text(f)
        parsed = parse_basic_sections(txt)
        docs.append({"id": f"doc_{i}", "text": txt, "source": f, "parsed": parsed})
    # assume resume is docs[0], jobs are docs[1:]
    resume = docs[0]
    jobs = docs[1:]
    vecs_jobs, metas_jobs = build_doc_embeddings(jobs)
    emb = Embedder()
    resume_vec = doc_level_embedding(resume["text"], emb)
    matches = match_resume_to_jobs(resume_vec, vecs_jobs, metas_jobs, top_k=3)
    print("Matches:", matches)
