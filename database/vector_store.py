import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from models.resume_models import Resume, JobPosting

class VectorStore:
    def __init__(self, storage_path: str = "data/vector_store.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.resumes: List[Resume] = []
        self.jobs: List[JobPosting] = []
        self.load_data()
    
    def load_data(self):
        """Load data from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.resumes = [Resume(**r) for r in data.get('resumes', [])]
                    self.jobs = [JobPosting(**j) for j in data.get('jobs', [])]
                    print(f"Loaded {len(self.resumes)} resumes and {len(self.jobs)} jobs")
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.resumes = []
                self.jobs = []
    
    def save_data(self):
        """Save data to storage."""
        data = {
            'resumes': [r.dict() for r in self.resumes],
            'jobs': [j.dict() for j in self.jobs]
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_resume(self, resume: Resume):
        """Add a resume to the store."""
        resume.id = f"resume_{len(self.resumes) + 1}"
        self.resumes.append(resume)
        self.save_data()
        print(f"✓ Resume added: {resume.name} (ID: {resume.id})")
    
    def add_job(self, job: JobPosting):
        """Add a job posting to the store."""
        job.id = f"job_{len(self.jobs) + 1}"
        self.jobs.append(job)
        self.save_data()
        print(f"✓ Job added: {job.title} at {job.company} (ID: {job.id})")
    
    def get_resume_by_id(self, resume_id: str) -> Optional[Resume]:
        """Get resume by ID."""
        return next((r for r in self.resumes if r.id == resume_id), None)
    
    def get_job_by_id(self, job_id: str) -> Optional[JobPosting]:
        """Get job by ID."""
        return next((j for j in self.jobs if j.id == job_id), None)
    
    def list_resumes(self) -> List[Dict[str, Any]]:
        """List all resumes with basic info."""
        return [{"id": r.id, "name": r.name, "skills": len(r.skills)} for r in self.resumes]
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs with basic info."""
        return [{"id": j.id, "title": j.title, "company": j.company, "skills": len(j.required_skills)} for j in self.jobs]