from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ContactInfo(BaseModel):
    emails: List[str] = []
    phones: List[str] = []
    linkedin: Optional[str] = None
    github: Optional[str] = None

class Experience(BaseModel):
    company: str
    position: str
    duration: str
    description: List[str] = []

class Education(BaseModel):
    institution: str
    degree: str
    duration: str

class Resume(BaseModel):
    id: Optional[str] = None
    file_path: str
    name: str
    contacts: ContactInfo
    skills: List[str]
    experience: List[Experience] = []
    education: List[Education] = []
    raw_text: str
    embedding: Optional[List[float]] = None

class JobPosting(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    description: str
    required_skills: List[str]
    raw_text: str
    embedding: Optional[List[float]] = None

class MatchResult(BaseModel):
    resume: Resume
    job: JobPosting
    similarity_score: float
    matching_skills: List[str]
    explanation: str