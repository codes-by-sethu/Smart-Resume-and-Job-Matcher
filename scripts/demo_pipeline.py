# scripts/demo_pipeline.py
import sys
from ingestion.parsers import extract_text, parse_basic_sections
from app.embeddings import Embedder, build_index_from_documents, save_index, load_index
from app.retriever import retrieve
from pathlib import Path
import json

def demo_from_files(file_list):
    docs = []
    for i, p in enumerate(file_list):
        text = extract_text(p)
        parsed = parse_basic_sections(text)
        docs.append({
            "id": f"doc_{i}",
            "text": text,
            "source": Path(p).name,
            "section": "full",
            "parsed": parsed
        })
    emb = Embedder()
    index, metas = build_index_from_documents(docs, emb)
    out_dir = "data/index_demo"
    save_index(index, metas, out_dir)
    print("Index built and saved to", out_dir)
    # simple interactive query
    while True:
        q = input("\nEnter query (or 'exit'): ").strip()
        if not q or q.lower() == "exit":
            break
        idx, metadata = load_index(out_dir)
        results = retrieve(q, idx, metadata, top_k=5, embedder=emb)
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/demo_pipeline.py resume_or_job1.pdf resume_or_job2.docx ...")
        sys.exit(1)
    demo_from_files(sys.argv[1:])
