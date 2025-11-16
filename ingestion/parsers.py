import re
from pathlib import Path
from typing import Dict, Any
import pdfplumber
import docx

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
PHONE_RE = re.compile(r"(\+?\d{1,3})?[\s\-.(]*\d{2,4}[\s\-.)]*\d{2,4}[\s\-]*\d{2,4}")

SECTION_HEADERS = [
    r"\beducation\b",
    r"\bexperience\b",
    r"\bwork experience\b",
    r"\bprofessional experience\b",
    r"\bskills\b",
    r"\bcertifications\b",
    r"\bprojects\b",
    r"\binterests\b",
]

def extract_text(path: str) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    text = ""
    if suffix == ".pdf":
        try:
            with pdfplumber.open(path) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                text = "\n".join(pages)
        except Exception:
            # fallback: read binary and attempt decode (best-effort)
            text = path.read_bytes().decode(errors="ignore")
    elif suffix in [".docx", ".doc"]:
        try:
            doc = docx.Document(path)
            paragraphs = [p.text for p in doc.paragraphs]
            text = "\n".join(paragraphs)
        except Exception:
            text = path.read_bytes().decode(errors="ignore")
    else:
        # txt or unknown -> try text
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = path.read_bytes().decode(errors="ignore")
    return text

def extract_contacts(text: str) -> Dict[str, Any]:
    emails = list(set(EMAIL_RE.findall(text)))
    phones = list(set(PHONE_RE.findall(text)))
    # PHONE_RE may capture groups; flatten sensible values
    phones_clean = []
    for m in PHONE_RE.finditer(text):
        phones_clean.append(m.group(0))
    phones_clean = list(dict.fromkeys(phones_clean))
    return {"emails": emails, "phones": phones_clean}

def split_sections(text: str) -> Dict[str, str]:
    """
    Very simple section splitter by header keywords.
    Returns dict header -> section text.
    """
    lines = text.splitlines()
    header_indices = []
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if any(re.search(h, low) for h in SECTION_HEADERS):
            header_indices.append((i, line.strip()))
    sections = {}
    if not header_indices:
        sections["full"] = text
        return sections

    # append sentinel end
    header_indices.append((len(lines), "__end__"))
    for (start_idx, header), (end_idx, _) in zip(header_indices[:-1], header_indices[1:]):
        sect_lines = lines[start_idx+1:end_idx]
        key = header.lower()
        sections[key] = "\n".join(sect_lines).strip()
    # Also include raw full text
    sections["full"] = text
    return sections

def parse_basic_sections(text: str) -> Dict[str, Any]:
    contacts = extract_contacts(text)
    sections = split_sections(text)
    # small heuristic skill extraction: look for lines containing common separators or commas in skills sections
    skills = []
    for k in sections:
        if "skill" in k:
            # split by commas or bullets
            chunk = sections[k]
            parts = re.split(r"[\n•\-\*;]+", chunk)
            for p in parts:
                p = p.strip()
                if len(p) > 1 and len(p.split()) <= 6:
                    skills.extend([s.strip() for s in re.split(r",", p) if s.strip()])
    # fallback: try to find "skills:" inline
    if not skills:
        m = re.search(r"skills\s*[:\-]\s*(.+)", text, re.IGNORECASE)
        if m:
            skills = [s.strip() for s in re.split(r"[;,]", m.group(1)) if s.strip()]

    return {
        "contacts": contacts,
        "skills": skills,
        "sections": sections
    }

if __name__ == "__main__":
    # quick test
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python ingestion/parsers.py <resume.pdf/docx/txt>")
        sys.exit(1)
    path = sys.argv[1]
    txt = extract_text(path)
    parsed = parse_basic_sections(txt)
    print("=== Contacts ===")
    print(json.dumps(parsed["contacts"], indent=2))
    print("\n=== Skills (sample) ===")
    print(parsed["skills"][:20])
    print("\n=== Sections keys ===")
    print(list(parsed["sections"].keys()))
