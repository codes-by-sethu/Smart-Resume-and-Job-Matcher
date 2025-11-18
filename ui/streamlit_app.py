import streamlit as st
from ingestion.parsers import extract_text, parse_basic_sections
from app.matcher import build_doc_embeddings, doc_level_section_embedding, match_resume_to_jobs
from app.explain import generate_explanation
from app.embeddings import Embedder
from pathlib import Path
import tempfile
import json

st.set_page_config(page_title="Smart Resume & Job Matcher", layout="centered")
st.title("Smart Resume & Job Matcher (Prototype)")

# Sidebar uploads
st.sidebar.header("Upload documents")
resume_files = st.sidebar.file_uploader("Upload resume(s)", type=['pdf','docx','txt'], accept_multiple_files=True)
job_files = st.sidebar.file_uploader("Upload job(s)", type=['pdf','docx','txt'], accept_multiple_files=True)

if 'indexed' not in st.session_state:
    st.session_state['indexed'] = False

if st.sidebar.button("Index uploaded documents"):
    if not resume_files and not job_files:
        st.sidebar.warning("Upload at least one resume or job file.")
    else:
        tmpdir = Path(tempfile.mkdtemp())
        docs = []

        # Save and process uploads
        for f in resume_files + job_files:
            path = tmpdir / f.name
            path.write_bytes(f.getbuffer())
            txt = extract_text(path)
            parsed = parse_basic_sections(txt)
            docs.append({"id": f.name, "text": txt, "source": f.name, "parsed": parsed})

        emb = Embedder()
        doc_vecs, doc_metas = build_doc_embeddings(docs, emb)

        # Store in session
        st.session_state.update({
            'indexed': True,
            'tmpdir': str(tmpdir),
            'docs': docs,
            'doc_vecs': doc_vecs,
            'doc_metas': doc_metas
        })
        st.success(f"Indexed {len(docs)} documents. Ready for matching.")

# Matching interface
if st.session_state.get('indexed', False):
    st.header("Match Resume to Jobs")
    docs = st.session_state['docs']
    emb = Embedder()

    # Allow selecting one or multiple resumes
    resume_names = [d['source'] for d in docs if d['source'].lower().endswith(('.pdf','.docx','.txt'))]
    selected_resume_name = st.selectbox("Select resume to match", resume_names)
    resume_doc = next(d for d in docs if d['source'] == selected_resume_name)

    # Job docs exclude selected resume
    job_docs = [d for d in docs if d['source'] != selected_resume_name]

    if job_docs and st.button("Find top matches"):
        resume_vec = doc_level_section_embedding(resume_doc['parsed'], emb)
        job_vecs, job_metas = build_doc_embeddings(job_docs, emb)
        matches = match_resume_to_jobs(resume_vec, job_vecs, job_metas, top_k=5)

        st.write("Top Matches:")
        for m in matches:
            job_doc = job_docs[m['job_index']]
            st.subheader(f"{m['job_source']} — Score: {m['score']:.4f}")
            st.markdown("**Job snippet:**")
            st.text(job_doc['text'][:800])

            with st.spinner("Generating explanation..."):
                expl = generate_explanation(resume_doc['parsed'], job_doc['parsed'], m['score'])
            st.markdown("**Explanation:**")
            st.write(expl)

st.write("---")
st.markdown("Tip: For production, persist indexes and allow multiple resumes/jobs selection UX.")
