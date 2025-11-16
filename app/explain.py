# app/explain.py
import os
import requests
from typing import Dict, Any, List, Optional

# By default, we use the local Ollama REST endpoint at http://localhost:11434
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

def _call_ollama_rest(prompt: str, model: str = OLLAMA_MODEL, temperature: float = 0.0, max_tokens: int = 256) -> str:
    """
    Simple non-streaming REST call to the local Ollama server.
    Returns the content string on success, or raises on failure.
    """
    url = OLLAMA_HOST.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant that explains resume-to-job matches. Be factual and cite the candidate's listed skills/experience."},
            {"role": "user", "content": prompt}
        ],
        "options": {"temperature": temperature},
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    # Ollama returns {"message": {"content": "..."}}
    return data.get("message", {}).get("content", "")

def generate_explanation(resume_parsed: Dict[str, Any], job_parsed: Dict[str, Any], similarity_score: float, top_n_evidence: int = 3) -> str:
    """
    resume_parsed: output from parse_basic_sections -> contains sections and skills
    job_parsed: same structure for job posting
    similarity_score: numeric
    Returns a short explanation text.
    """
    # Build concise summaries to include in prompt (keep within token limits)
    resume_skills = resume_parsed.get("skills", [])
    resume_summary = []
    # try to extract short highlights: executive summary + first work experience preview
    sections = resume_parsed.get("sections", {})
    exec_summary = ""
    if "executive summary" in "".join(sections.keys()).lower():
        # attempt to find a line with "executive summary"
        for k in sections:
            if "executive summary" in k.lower():
                exec_summary = sections[k][:400]
                break
    # fallback: take first 400 chars of full
    if not exec_summary:
        exec_summary = (sections.get("full", "")[:400]).replace("\n", " ")

    # job summary: extract required skills line if present
    job_text = job_parsed.get("sections", {}).get("full", "")
    # Job short snippet
    job_snippet = job_text[:600].replace("\n", " ")

    prompt = f"""
Candidate summary:
{exec_summary}

Candidate skills (extracted): {', '.join(resume_skills[:15])}

Job posting snippet:
{job_snippet}

Similarity score: {similarity_score:.4f}

Task: In 3-5 concise bullet points, explain why this candidate is a good (or not good) match for the role. For each bullet, cite which part of the candidate (skill or experience) maps to which part of the job posting. Keep it short and factual.
"""

    try:
        text = _call_ollama_rest(prompt, model=OLLAMA_MODEL, temperature=0.0, max_tokens=256)
    except Exception as e:
        # fallback explanation if Ollama isn't available
        text = "Could not call Ollama to generate explanation. Fallback: \n"
        text += f"- Similarity score: {similarity_score:.3f}\n"
        if resume_skills:
            text += f"- Candidate lists skills: {', '.join(resume_skills[:10])}\n"
        text += "- Evidence extraction unavailable (Ollama call failed). Error: " + str(e)
    return text

if __name__ == "__main__":
    # local smoke test (adjust file paths)
    from ingestion.parsers import extract_text, parse_basic_sections
    resume_txt = extract_text("data/sample_resume.pdf")
    resume_parsed = parse_basic_sections(resume_txt)
    job_txt = extract_text("data/sample_job1.txt")
    job_parsed = parse_basic_sections(job_txt)
    expl = generate_explanation(resume_parsed, job_parsed, similarity_score=0.12)
    print(expl)
