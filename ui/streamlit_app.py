# ui/streamlit_app.py
import streamlit as st
from ingestion.parsers import extract_text, parse_basic_sections
from app.embeddings import Embedder, build_index_from_documents, save_index, load_index
from app.matcher import build_doc_embeddings, doc_level_embedding, match_resume_to_jobs
from app.explain import generate_explanation
from pathlib import Path
import tempfile
import os
import json

st.set_page_config(page_title="Smart Resume & Job Matcher", layout="centered")

st.title("Smart Resume & Job Matcher (Prototype)")

# Upload resume(s) and job(s)
st.sidebar.header("Upload documents")
resume_file = st.sidebar.file_uploader("Upload resume (PDF/DOCX/TXT)", type=['pdf', 'docx', 'txt'])
job_files = st.sidebar.file_uploader("Upload job posting(s)", type=['txt', 'pdf', 'docx'], accept_multiple_files=True)

if 'indexed' not in st.session_state:
    st.session_state['indexed'] = False
if 'index_meta_path' not in st.session_state:
    st.session_state['index_meta_path'] = None

if st.sidebar.button("Index uploaded documents"):
    docs = []
    tmpdir = Path(tempfile.mkdtemp())
    # save uploaded files temporarily
    uploads = []
    if resume_file:
        p = tmpdir / resume_file.name
        p.write_bytes(resume_file.getbuffer())
        uploads.append(str(p))
    for jf in job_files:
        p = tmpdir / jf.name
        p.write_bytes(jf.getbuffer())
        uploads.append(str(p))
    if not uploads:
        st.sidebar.warning("Upload at least one resume or job file.")
    else:
        # create docs list
        for i, path in enumerate(uploads):
            txt = extract_text(path)
            parsed = parse_basic_sections(txt)
            docs.append({"id": f"doc_{i}", "text": txt, "source": Path(path).name, "parsed": parsed})
        emb = Embedder()
        # Build and save doc-level index (document vectors) to session tmp dir
        jobvecs, metas = build_doc_embeddings(docs)
        # Save meta to a temp path for later
        meta_path = tmpdir / "doc_metas.json"
        meta_path.write_text(json.dumps(metas, indent=2), encoding="utf-8")
        # save docs themselves so later we can find resume vs jobs (simple)
        docs_path = tmpdir / "docs.json"
        docs_path.write_text(json.dumps(docs, indent=2), encoding="utf-8")
        st.session_state['indexed'] = True
        st.session_state['tmpdir'] = str(tmpdir)
        st.session_state['doc_vecs'] = jobvecs.tolist()
        st.session_state['doc_metas'] = metas
        st.success(f"Indexed {len(docs)} documents. You can now match a resume to job(s).")

if st.session_state.get('indexed', False):
    st.header("Matching")
    # load docs metadata
    metas = st.session_state['doc_metas']
    docs = json.loads(Path(st.session_state['tmpdir']) / "docs.json".read_text(encoding="utf-8")) if False else None
    # We'll reconstruct docs list from metas file saved earlier
    tmpdir = Path(st.session_state['tmpdir'])
    docs = json.loads((tmpdir / "docs.json").read_text(encoding="utf-8"))
    # assume first uploaded is resume (simple UI flow)
    resume_candidates = [d for d in docs if 'resume' in d['source'].lower() or d['source'].lower().endswith('.pdf') or 'resume' in d['source'].lower()]
    # fallback: allow user to select which doc is resume
    doc_names = [d['source'] for d in docs]
    selected_resume = st.selectbox("Select resume document", options=doc_names, index=0)
    selected_resume_doc = next(d for d in docs if d['source'] == selected_resume)
    # build job vectors and metas (exclude resume)
    job_docs = [d for d in docs if d['source'] != selected_resume]
    if not job_docs:
        st.info("No job docs uploaded. Upload job postings to match against.")
    else:
        if st.button("Find top matches"):
            emb = Embedder()
            resume_vec = doc_level_embedding(selected_resume_doc['text'], emb)
            job_vecs, job_metas = build_doc_embeddings(job_docs, emb)
            matches = match_resume_to_jobs(resume_vec, job_vecs, job_metas, top_k=5)
            st.write("Top matches:")
            for m in matches:
                st.subheader(f"{m['job_source']}  — score {m['score']:.4f}")
                # show parsed job snippet
                job_meta = m['job_meta']
                job_index = m['job_index']
                job_doc = job_docs[job_index]
                st.markdown("**Job snippet:**")
                st.text(job_doc['text'][:800])
                # show explanation via Ollama
                with st.spinner("Generating explanation..."):
                    expl = generate_explanation(selected_resume_doc['parsed'], job_doc['parsed'], m['score'])
                st.markdown("**Explanation:**")
                st.write(expl)

st.write("---")
st.markdown("Tip: For production-ready demo, persist indexes to disk and support multiple resumes/jobs selection UX.")
