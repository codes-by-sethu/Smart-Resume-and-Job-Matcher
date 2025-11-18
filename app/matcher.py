from typing import List, Dict, Tuple
import numpy as np
from app.embeddings import Embedder
from pathlib import Path

# Section weights for embeddings
SECTION_WEIGHTS = {"skills": 0.5, "experience": 0.3, "education": 0.2}

def doc_level_section_embedding(parsed_doc: Dict, embedder: Embedder = None) -> np.ndarray:
    """
    Create a single vector for the document using weighted sections.
    """
    if embedder is None:
        embedder = Embedder()
    
    vectors = []
    weights = []

    # Skills
    if skills := parsed_doc.get("skills", []):
        text = ", ".join(skills)
        vectors.append(embedder.encode([text])[0])
        weights.append(SECTION_WEIGHTS["skills"])

    # Experience
    if exp := parsed_doc.get("sections", {}).get("experience", ""):
        vectors.append(embedder.encode([exp])[0])
        weights.append(SECTION_WEIGHTS["experience"])

    # Education
    if edu := parsed_doc.get("sections", {}).get("education", ""):
        vectors.append(embedder.encode([edu])[0])
        weights.append(SECTION_WEIGHTS["education"])

    if not vectors:
        return embedder.encode([""])[0]

    # Weighted average
    weighted_vec = sum(v * w for v, w in zip(vectors, weights)) / sum(weights)
    return weighted_vec / np.linalg.norm(weighted_vec)


def build_doc_embeddings(documents: List[Dict], embedder: Embedder = None) -> Tuple[np.ndarray, List[Dict]]:
    """
    Returns normalized vectors for all documents and metadata.
    Uses section-weighted embeddings if parsed is available.
    """
    if embedder is None:
        embedder = Embedder()
    
    vecs = []
    metas = []

    for d in documents:
        if parsed := d.get("parsed"):
            vec = doc_level_section_embedding(parsed, embedder)
        else:
            vec = embedder.encode([d.get("text", "")])[0]
        vecs.append(vec.astype("float32"))
        metas.append({"id": d.get("id"), "source": d.get("source"), "parsed": parsed or {}})
    
    return np.stack(vecs), metas


def match_resume_to_jobs(resume_vec: np.ndarray, job_vecs: np.ndarray, job_metas: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Cosine similarity (dot product) between resume vector and job vectors.
    Returns top-k matches with metadata.
    """
    # Ensure shapes
    if job_vecs.ndim == 1:
        job_vecs = job_vecs.reshape(1, -1)
    if resume_vec.ndim == 2 and resume_vec.shape[0] == 1:
        resume_vec = resume_vec.reshape(-1)
    elif resume_vec.ndim > 2:
        resume_vec = resume_vec.reshape(-1)

    sims = job_vecs @ resume_vec
    sims = np.asarray(sims).reshape(-1)

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
    # Demo using sample files
    from ingestion.parsers import extract_text, parse_basic_sections
    sample_files = ["data/sample_resume.pdf", "data/sample_job1.txt", "data/sample_job2.txt"]
    docs = []
    for i, f in enumerate(sample_files):
        txt = extract_text(f)
        parsed = parse_basic_sections(txt)
        docs.append({"id": f"doc_{i}", "text": txt, "source": f, "parsed": parsed})

    resume = docs[0]
    jobs = docs[1:]

    emb = Embedder()
    vecs_jobs, metas_jobs = build_doc_embeddings(jobs, emb)
    resume_vec = doc_level_section_embedding(resume["parsed"], emb)

    matches = match_resume_to_jobs(resume_vec, vecs_jobs, metas_jobs, top_k=3)
    print("Top Matches:")
    for m in matches:
        print(f"{m['job_source']} — Score: {m['score']:.4f}")
