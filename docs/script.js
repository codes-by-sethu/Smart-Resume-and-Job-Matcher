// Store uploaded files
let resumes = [];
let jobs = [];

// File upload handlers
document.getElementById('resumeUpload').addEventListener('change', function(e) {
    handleFileUpload(e.target.files, resumes, 'resumeList');
});

document.getElementById('jobUpload').addEventListener('change', function(e) {
    handleFileUpload(e.target.files, jobs, 'jobList');
});

function handleFileUpload(files, storage, listId) {
    Array.from(files).forEach(file => {
        if (!storage.find(f => f.name === file.name)) {
            storage.push(file);
            updateFileList(listId, storage);
        }
    });
}

function updateFileList(listId, files) {
    const list = document.getElementById(listId);
    list.innerHTML = files.map(file => 
        `<div class="file-item">${file.name}</div>`
    ).join('');
}

// Process documents (this would call your backend API)
async function processDocuments() {
    if (resumes.length === 0 && jobs.length === 0) {
        alert('Please upload at least one resume or job description');
        return;
    }

    const btn = document.getElementById('processBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        // In a real implementation, you would:
        // 1. Send files to your backend API
        // 2. Wait for processing to complete
        // 3. Update the resume dropdown
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Update resume dropdown
        const select = document.getElementById('resumeSelect');
        select.innerHTML = '<option value="">Select a resume...</option>' +
            resumes.map(resume => 
                `<option value="${resume.name}">${resume.name}</option>`
            ).join('');
        
        alert(`Successfully processed ${resumes.length} resumes and ${jobs.length} jobs!`);
    } catch (error) {
        alert('Error processing documents: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Process Documents';
    }
}

// Find matches (this would call your matching API)
async function findMatches() {
    const resumeSelect = document.getElementById('resumeSelect');
    const selectedResume = resumeSelect.value;
    
    if (!selectedResume) {
        alert('Please select a resume first');
        return;
    }

    const btn = document.getElementById('matchBtn');
    btn.disabled = true;
    btn.textContent = 'Finding Matches...';

    try {
        // Simulate API call to your matching backend
        const results = await simulateMatchingAPI(selectedResume);
        displayResults(results);
    } catch (error) {
        alert('Error finding matches: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Find Job Matches';
    }
}

// Simulate matching results (replace with actual API call)
async function simulateMatchingAPI(resumeName) {
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock data - replace with actual API response
    return [
        {
            job: {
                title: "Data Scientist",
                company: "Tech Corp",
                description: "Looking for data scientist with Python and ML experience..."
            },
            similarity_score: 0.87,
            matching_skills: ["Python", "Machine Learning", "Pandas", "SQL"],
            explanation: "Strong match! The candidate's experience in machine learning and Python aligns perfectly with the role requirements. Their background in data analysis using Pandas and SQL is exactly what we're looking for."
        },
        {
            job: {
                title: "AI Research Engineer", 
                company: "AI Labs",
                description: "Research position focusing on AI governance and ethical AI..."
            },
            similarity_score: 0.76,
            matching_skills: ["AI Governance", "Python", "Research"],
            explanation: "Good match for research-focused role. The candidate's AI governance experience is valuable, though they may need more specific research methodology experience."
        },
        {
            job: {
                title: "Data Analyst",
                company: "Analytics Inc", 
                description: "Junior data analyst position with focus on SQL and visualization..."
            },
            similarity_score: 0.65,
            matching_skills: ["SQL", "Data Analysis", "Python"],
            explanation: "Reasonable match for junior position. Strong technical skills but may be overqualified for this role."
        }
    ];
}

function displayResults(results) {
    const container = document.getElementById('results');
    
    if (results.length === 0) {
        container.innerHTML = '<p>No matches found. Try uploading more job descriptions.</p>';
        return;
    }

    container.innerHTML = results.map(result => `
        <div class="match-card">
            <div class="match-header">
                <h3>${result.job.title} at ${result.job.company}</h3>
                <div class="match-score">${(result.similarity_score * 100).toFixed(0)}% Match</div>
            </div>
            <p><strong>Description:</strong> ${result.job.description.substring(0, 150)}...</p>
            <div class="skills-list">
                ${result.matching_skills.map(skill => 
                    `<span class="skill-tag">${skill}</span>`
                ).join('')}
            </div>
            <div class="explanation">
                <strong>AI Analysis:</strong> ${result.explanation}
            </div>
        </div>
    `).join('');
}