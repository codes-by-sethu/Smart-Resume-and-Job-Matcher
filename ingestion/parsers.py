import re
from pathlib import Path
from typing import Dict, Any, List
import pdfplumber
import docx
import json
import sys

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")

PHONE_RE = re.compile(
    r"""
    (?:[\+]?\d{1,3}[-.\s]?)?      # country code
    \(?\d{0,4}\)?[-.\s]?          # area code
    \d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{0,4}  # main number with optional parts
    """,
    re.VERBOSE
)

SECTION_HEADERS = [
    r"education",
    r"experience",
    r"work\s+experience",
    r"professional\s+experience",
    r"skills",
    r"technical\s+skills",
    r"certifications",
    r"projects",
    r"academic\s+projects",
    r"interests",
    r"summary",
    r"executive\s+summary",
    r"objective",
    r"achievements",
    r"publications",
    r"languages",
]

def extract_text(path: str) -> str:
    """Extract text from PDF, DOCX, DOC, or text files."""
    path = Path(path)
    suffix = path.suffix.lower()
    text = ""
    
    if suffix == ".pdf":
        try:
            with pdfplumber.open(path) as pdf:
                pages = []
                for p in pdf.pages:
                    page_text = p.extract_text() or ""
                    if page_text:
                        # Use layout preservation for better structure
                        page_text = re.sub(r'[ \t]+', ' ', page_text)
                        pages.append(page_text)
                text = "\n".join(pages)
        except Exception as e:
            print(f"PDF extraction failed, using fallback: {e}")
            try:
                text = path.read_bytes().decode('utf-8', errors='ignore')
            except:
                text = path.read_bytes().decode('latin-1', errors='ignore')
    
    elif suffix in [".docx", ".doc"]:
        try:
            doc = docx.Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
        except Exception as e:
            print(f"DOCX extraction failed, using fallback: {e}")
            try:
                text = path.read_bytes().decode('utf-8', errors='ignore')
            except:
                text = path.read_bytes().decode('latin-1', errors='ignore')
    
    else:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Text extraction failed, using fallback: {e}")
            try:
                text = path.read_bytes().decode('utf-8', errors='ignore')
            except:
                text = path.read_bytes().decode('latin-1', errors='ignore')
    
    # Clean up but preserve meaningful structure
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_contacts(text: str) -> Dict[str, Any]:
    """Extract email addresses and phone numbers from text."""
    emails = list(set(EMAIL_RE.findall(text)))
    
    phones = []
    # More flexible phone matching to capture full numbers
    phone_patterns = [
        r'[\+]?[\(\d][\d\s\(\)\.\-]{7,20}\d',  # General phone pattern
        r'\+\d{1,3}[\s\-]?\(?\d\)?[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}',  # International format
    ]
    
    for pattern in phone_patterns:
        for match in re.finditer(pattern, text):
            phone = match.group(0).strip()
            digits_only = re.sub(r'\D', '', phone)
            
            # Validate phone number
            if (8 <= len(digits_only) <= 15 and
                not re.search(r'(?:19|20)\d{2}', digits_only)):
                # Clean but keep original format
                phone_clean = re.sub(r'\s+', ' ', phone)
                if phone_clean not in phones:
                    phones.append(phone_clean)
    
    return {"emails": emails, "phones": phones}

def extract_name(text: str) -> str:
    """Extract probable name from resume text."""
    lines = text.split('\n')
    for line in lines[:10]:
        line = line.strip()
        # Look for lines that look like names (title case, reasonable length)
        if (2 <= len(line) <= 50 and
            re.match(r'^[A-Z][a-zA-Z\s\-\.]+$', line) and
            len(line.split()) in [2, 3] and
            not any(word in line.lower() for word in 
                   ['email', 'phone', 'linkedin', 'github', 'resume', 'cv', 
                    'summary', 'objective', 'experience', 'education'])):
            return line
    return ""

def extract_skills_from_content(content: str) -> List[str]:
    """Extract skills from a content block with better handling of compound skills."""
    if not content:
        return []
    
    # Common non-skill words to exclude
    non_skills = {'tools', 'programming', 'languages', 'frameworks', 'skills', 
                  'technical', 'proficient', 'experienced', 'knowledge', 'model',
                  'evaluation', 'monitoring', 'handling', 'processing'}
    
    skills = []
    
    # First, extract compound skills that are clearly separated
    compound_patterns = [
        r'([A-Z][a-zA-Z\s&]+(?:\([^)]+\))?:\s*[^:\n]+)',  # "Category: skill1, skill2"
        r'([A-Z][a-zA-Z\s&]+(?:\([^)]+\))?[:\-]\s*[^:\n]+)',  # "Category - skill1, skill2"
    ]
    
    for pattern in compound_patterns:
        for match in re.finditer(pattern, content):
            category_block = match.group(1)
            # Split the skills within the category
            if ':' in category_block or '-' in category_block:
                parts = re.split(r'[:,]', category_block, maxsplit=1)
                if len(parts) > 1:
                    skill_part = parts[1]
                    individual_skills = re.split(r'[,;]', skill_part)
                    for skill in individual_skills:
                        skill_clean = skill.strip()
                        if (skill_clean and 
                            skill_clean.lower() not in non_skills and
                            2 <= len(skill_clean) <= 40):
                            skills.append(skill_clean)
    
    # Then extract individual skills from the content
    lines = content.split('\n')
    for line in lines:
        line_clean = re.sub(r'[\(\)]', ' ', line)  # Replace parentheses with spaces
        parts = re.split(r'[\n•\-\*;:,/&]', line_clean)
        
        for part in parts:
            part = part.strip()
            if not part or part in ['•', '-', '*', ':', '']:
                continue
                
            # Skip if it's a category header (ends with colon or contains specific patterns)
            if (part.endswith(':') or 
                'governance &' in part.lower() or
                'programming &' in part.lower() or
                'model' in part.lower() and 'evaluation' in part.lower()):
                continue
                
            # Clean the part
            part_clean = re.sub(r'^[\s\(\[]+|[\s\)\]]+$', '', part)
            part_clean = re.sub(r'\s+', ' ', part_clean).strip()
            
            # Skill validation
            if (2 <= len(part_clean) <= 50 and
                part_clean.lower() not in non_skills and
                len(part_clean.split()) <= 4 and
                not re.search(r'\b(?:19|20)\d{2}\b', part_clean) and
                not part_clean.isdigit() and
                not part_clean.startswith(('http://', 'https://', 'www.'))):
                
                skills.append(part_clean)
    
    return skills

def extract_skills(text: str, sections: Dict[str, str]) -> List[str]:
    """Extract skills from sections and text."""
    skills = []
    
    # Priority 1: Skills section (most reliable)
    for section_name, content in sections.items():
        if 'skill' in section_name.lower():
            section_skills = extract_skills_from_content(content)
            skills.extend(section_skills)
    
    # Priority 2: Common tech skills pattern matching
    common_skill_groups = {
        'programming': ['python', 'sql', 'java', 'javascript', 'c++', 'r'],
        'ml_frameworks': ['tensorflow', 'pytorch', 'scikit-learn', 'keras'],
        'data_tools': ['pandas', 'numpy', 'jupyter', 'colab', 'tableau'],
        'ml_techniques': ['machine learning', 'supervised learning', 'unsupervised learning', 
                         'regression', 'svm', 'knn', 'decision trees', 'random forests'],
        'ai_areas': ['ai governance', 'responsible ai', 'model risk assessment', 
                    'compliance frameworks', 'bias evaluation', 'fairness evaluation'],
        'apis': ['openai api', 'gpt-4', 'gpt']
    }
    
    text_lower = text.lower()
    for category, skill_list in common_skill_groups.items():
        for skill in skill_list:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                formatted_skill = skill.title() if skill.islower() and len(skill) > 2 else skill.upper()
                if formatted_skill not in skills:
                    skills.append(formatted_skill)
    
    # Priority 3: Extract from other technical sections
    technical_sections = ['experience', 'projects', 'work', 'academic']
    for section_name, content in sections.items():
        if any(tech in section_name.lower() for tech in technical_sections):
            section_skills = extract_skills_from_content(content)
            skills.extend(section_skills)
    
    # Clean and deduplicate
    seen = set()
    unique_skills = []
    for skill in skills:
        skill_lower = skill.lower()
        if (skill_lower not in seen and 
            skill.strip() and 
            len(skill.strip()) > 1 and
            not skill_lower.endswith(':')):
            seen.add(skill_lower)
            unique_skills.append(skill.strip())
    
    return sorted(unique_skills, key=lambda x: x.lower())

def split_sections(text: str) -> Dict[str, str]:
    """Split resume text into sections based on headers."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) <= 1:
        return {"full": text}
    
    header_indices = []
    
    # Identify section headers with more flexible matching
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Clean the line for matching
        line_clean = re.sub(r'[^a-zA-Z\s]', ' ', line_lower)
        line_clean = re.sub(r'\s+', ' ', line_clean).strip()
        
        # Check against all section header patterns
        for header_pattern in SECTION_HEADERS:
            pattern = r'^' + header_pattern + r'$'
            if re.search(pattern, line_clean):
                header_indices.append((i, line))
                break
    
    sections = {"full": text}
    
    if not header_indices:
        return sections
    
    # Sort by position and add end marker
    header_indices.sort(key=lambda x: x[0])
    header_indices.append((len(lines), "END"))
    
    # Extract content for each section
    for j in range(len(header_indices) - 1):
        start_idx, header = header_indices[j]
        end_idx, _ = header_indices[j + 1]
        
        # Get content between this header and next header
        section_content = []
        for k in range(start_idx + 1, end_idx):
            current_line = lines[k]
            # Check if current line is another header
            current_lower = current_line.lower()
            current_clean = re.sub(r'[^a-zA-Z\s]', ' ', current_lower)
            current_clean = re.sub(r'\s+', ' ', current_clean).strip()
            
            is_header = any(re.search(r'^' + pattern + r'$', current_clean) 
                          for pattern in SECTION_HEADERS)
            
            if not is_header:
                section_content.append(current_line)
            else:
                break
        
        if section_content:
            section_key = re.sub(r'[^a-zA-Z\s]', ' ', header.lower())
            section_key = re.sub(r'\s+', ' ', section_key).strip()
            sections[section_key] = "\n".join(section_content).strip()
    
    return sections

def parse_basic_sections(text: str) -> Dict[str, Any]:
    """Main parsing function that extracts all resume information."""
    contacts = extract_contacts(text)
    name = extract_name(text)
    sections = split_sections(text)
    skills = extract_skills(text, sections)
    
    return {
        "name": name,
        "contacts": contacts,
        "skills": skills,
        "sections": sections,
        "metadata": {
            "total_sections": len([k for k in sections.keys() if k != "full"]),
            "total_skills": len(skills),
            "has_contacts": len(contacts["emails"]) > 0 or len(contacts["phones"]) > 0
        }
    }

def analyze_resume_structure(text: str) -> Dict[str, Any]:
    """Additional analysis of resume structure."""
    lines = [line for line in text.split('\n') if line.strip()]
    word_count = len(text.split())
    line_count = len(lines)
    
    # Count actual section headers found
    section_count = 0
    for line in lines:
        line_clean = re.sub(r'[^a-zA-Z\s]', ' ', line.lower())
        line_clean = re.sub(r'\s+', ' ', line_clean).strip()
        if any(re.search(r'^' + header + r'$', line_clean) for header in SECTION_HEADERS):
            section_count += 1
    
    return {
        "word_count": word_count,
        "line_count": line_count,
        "detected_sections": section_count,
        "avg_line_length": sum(len(line) for line in lines) / max(1, line_count)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <resume.pdf/docx/txt>")
        print("Example: python resume_parser.py resume.pdf")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if not Path(path).exists():
        print(f"Error: File '{path}' not found")
        sys.exit(1)
    
    try:
        print(f"Processing: {path}")
        txt = extract_text(path)
        
        if not txt.strip():
            print("Error: No text could be extracted from the file")
            sys.exit(1)
        
        parsed = parse_basic_sections(txt)
        structure = analyze_resume_structure(txt)
        
        print("\n" + "="*50)
        print("RESUME ANALYSIS RESULTS")
        print("="*50)
        
        print(f"\nFile: {path}")
        print(f"Text length: {len(txt)} characters")
        print(f"Lines: {structure['line_count']}")
        print(f"Word count: {structure['word_count']}")
        print(f"Detected sections: {structure['detected_sections']}")
        
        print(f"\n=== Name ===")
        print(parsed["name"] if parsed["name"] else "Not detected")
        
        print(f"\n=== Contacts ===")
        print(json.dumps(parsed["contacts"], indent=2))
        
        print(f"\n=== Skills ({len(parsed['skills'])} found) ===")
        if parsed["skills"]:
            # Group skills by category for better readability
            categories = {
                "AI/ML": [s for s in parsed["skills"] if any(x in s.lower() for x in ['ai', 'machine', 'learning', 'model', 'bias', 'fairness'])],
                "Programming": [s for s in parsed["skills"] if any(x in s.lower() for x in ['python', 'sql', 'jupyter', 'colab', 'api'])],
                "Data Tools": [s for s in parsed["skills"] if any(x in s.lower() for x in ['pandas', 'numpy', 'data'])],
                "ML Techniques": [s for s in parsed["skills"] if any(x in s.lower() for x in ['supervised', 'unsupervised', 'regression', 'svm', 'knn', 'decision', 'random'])],
                "Other": [s for s in parsed["skills"] if not any(x in s.lower() for x in ['ai', 'machine', 'python', 'sql', 'pandas', 'numpy', 'supervised', 'unsupervised'])]
            }
            
            for category, skills in categories.items():
                if skills:
                    print(f"\n{category}:")
                    for i, skill in enumerate(skills[:10], 1):
                        print(f"  {i:2d}. {skill}")
                    if len(skills) > 10:
                        print(f"  ... and {len(skills) - 10} more")
        else:
            print("No skills detected")
        
        print(f"\n=== Sections ({parsed['metadata']['total_sections']} detected) ===")
        for section, content in parsed["sections"].items():
            if section != "full":
                word_count = len(content.split())
                lines = content.split('\n')
                preview = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
                if preview.strip():
                    print(f"- {section:25} ({word_count:3} words): {preview}")
        
        print(f"\n=== Structure Analysis ===")
        print(f"Average line length: {structure['avg_line_length']:.1f} chars")
        print(f"Has contact info: {parsed['metadata']['has_contacts']}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)