console.log("script.js loaded successfully");

let resumes = [];
let jobDescriptions = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing application');
    
    const processBtn = document.getElementById('processBtn');
    const matchBtn = document.getElementById('matchBtn');
    
    console.log('Buttons found:', {
        processBtn: processBtn ? 'Found' : 'NOT FOUND',
        matchBtn: matchBtn ? 'Found' : 'NOT FOUND'
    });
    
    if (processBtn) {
        processBtn.addEventListener('click', processDocuments);
        console.log('Process button event listener added');
    } else {
        console.error('Process button not found');
    }
    
    if (matchBtn) {
        matchBtn.addEventListener('click', findMatches);
        console.log('Match button event listener added');
    } else {
        console.error('Match button not found');
    }
    
    const resumeUpload = document.getElementById('resumeUpload');
    if (resumeUpload) {
        resumeUpload.addEventListener('change', function(e) {
            console.log('Resume upload changed:', e.target.files);
            handleFileUpload(e.target.files, resumes, 'resumeList');
        });
    }
    
    const jobDescription = document.getElementById('jobDescription');
    if (jobDescription) {
        jobDescription.addEventListener('input', function(e) {
            const description = e.target.value.trim();
            console.log('Job description input:', description.length, 'characters');
            if (description) {
                jobDescriptions = [{ 
                    name: 'Pasted Job Description', 
                    content: description, 
                    type: 'text',
                    id: 'pasted-' + Date.now()
                }];
                updateJobDescriptionList();
            } else {
                jobDescriptions = [];
                document.getElementById('jobList').innerHTML = '';
            }
        });
    }
    
    testBackendConnection();
    loadRealJobOpportunities();
    
    console.log('Application initialization complete');
});

async function testBackendConnection() {
    try {
        console.log('Testing backend connection');
        const response = await fetch('/health');
        const result = await response.json();
        console.log('Backend connection successful:', result);
    } catch (error) {
        console.error('Backend connection failed:', error);
        showError('Backend connection failed. Make sure the server is running.');
    }
}

function handleFileUpload(files, storage, listId) {
    console.log('Handling file upload:', files.length, 'files');
    
    Array.from(files).forEach(file => {
        const exists = storage.find(f => f.name === file.name);
        if (!exists) {
            storage.push({
                name: file.name,
                file: file,
                type: file.type,
                id: 'file-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
            });
            console.log('File added:', file.name);
        } else {
            console.log('File already exists:', file.name);
        }
    });
    
    updateFileList(listId, storage);
}

function updateFileList(listId, files) {
    const list = document.getElementById(listId);
    if (!list) {
        console.error('List element not found:', listId);
        return;
    }
    
    if (files.length === 0) {
        list.innerHTML = '<div class="file-item empty">No files uploaded</div>';
    } else {
        list.innerHTML = files.map(file => 
            `<div class="file-item">
                <span class="file-name">${file.name}</span>
                <button class="remove-btn" onclick="removeFile('${file.id}', '${listId}')">×</button>
            </div>`
        ).join('');
    }
}

function updateJobDescriptionList() {
    const list = document.getElementById('jobList');
    if (!list) {
        console.error('Job list element not found');
        return;
    }
    
    if (jobDescriptions.length > 0) {
        list.innerHTML = jobDescriptions.map(job => 
            `<div class="file-item">
                <span class="file-name">Pasted Job Description</span>
                <button class="remove-btn" onclick="removeJobDescription()">×</button>
            </div>`
        ).join('');
    } else {
        list.innerHTML = '<div class="file-item empty">No job description added</div>';
    }
}

function removeFile(fileId, listId) {
    console.log('Removing file:', fileId);
    if (listId === 'resumeList') {
        resumes = resumes.filter(f => f.id !== fileId);
        updateFileList(listId, resumes);
    }
}

function removeJobDescription() {
    console.log('Removing job description');
    jobDescriptions = [];
    const jobDescInput = document.getElementById('jobDescription');
    if (jobDescInput) {
        jobDescInput.value = '';
    }
    updateJobDescriptionList();
}

async function processDocuments() {
    console.log('PROCESS DOCUMENTS FUNCTION CALLED');
    
    if (resumes.length === 0) {
        showError('Please upload at least one resume file.');
        return;
    }
    
    const jobText = document.getElementById('jobDescription')?.value.trim();
    if (!jobText) {
        showError('Please add a job description.');
        return;
    }
    
    console.log('Validation passed, starting processing');
    
    const btn = document.getElementById('processBtn');
    if (!btn) {
        console.error('Process button not found');
        return;
    }
    
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Processing...';
    
    try {
        const analysisContent = document.getElementById('analysisContent');
        if (analysisContent) {
            analysisContent.innerHTML = `
                <div class="processing">
                    <div class="spinner"></div>
                    <h3>AI Analysis in Progress</h3>
                    <p>Step 1: Extracting text from resume...</p>
                    <p>Step 2: Parsing skills and experience...</p>
                    <p>Step 3: Building semantic embeddings...</p>
                    <p>Step 4: Calculating match score...</p>
                    <p class="progress-info">This may take 10-20 seconds for AI analysis</p>
                </div>
            `;
        }
        
        analysisContent?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        console.log('Sending request to backend');
        
        // ✅ FIXED BLOCK
        const formData = new FormData();
        formData.append('resume', resumes[0].file);
        formData.append('job_description', jobText);

        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        console.log('Response received, status:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server returned ${response.status}`);
        }

        const result = await response.json();
        console.log('Analysis successful:', result);

        displayAnalysisResults(result);
        updateResumeDropdown();

    } catch (error) {
        console.error('Processing error:', error);
        showError(`Analysis failed: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function displayAnalysisResults(result) {
    console.log('Displaying analysis results');

    const analysisContent = document.getElementById('analysisContent');
    if (!analysisContent) {
        console.error('Analysis content element not found');
        return;
    }

    analysisContent.innerHTML = `
        <div class="analysis-results">
            <div class="match-header">
                <div class="score-circle" style="--score: ${result.match_percentage}%">
                    <span class="score">${result.match_percentage}%</span>
                    <span class="score-label">AI Match Score</span>
                </div>
                <div class="match-explanation">
                    <h3>AI Powered Analysis Complete</h3>
                    <p><strong>Analysis Type:</strong> ${result.analysis_type || 'Semantic AI Matching'}</p>
                    <p>${result.explanation}</p>
                    <div class="stats">
                        <div class="stat">
                            <span class="stat-value">${result.matching_skills?.length || 0}</span>
                            <span class="stat-label">Matching Skills</span>
                        </div>
                        <div class="stat">
                            <span class="stat-value">${result.missing_skills?.length || 0}</span>
                            <span class="stat-label">Skills to Develop</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="skills-analysis">
                <div class="skills-column">
                    <h4>Matching Skills</h4>
                    <div class="skills-list">
                        ${result.matching_skills && result.matching_skills.length > 0 
                            ? result.matching_skills.map(skill => `<span class="skill-tag match">${skill}</span>`).join('')
                            : '<p class="no-skills">No matching skills detected</p>'
                        }
                    </div>
                </div>

                <div class="skills-column">
                    <h4>Skills to Develop</h4>
                    <div class="skills-list">
                        ${result.missing_skills && result.missing_skills.length > 0 
                            ? result.missing_skills.map(skill => `<span class="skill-tag missing">${skill}</span>`).join('')
                            : '<p class="no-skills">Excellent skill alignment</p>'
                        }
                    </div>
                </div>
            </div>

            <div class="ai-features">
                <h4>AI Powered Features Used</h4>
                <ul>
                    <li>Semantic Embedding Matching</li>
                    <li>Contextual Skill Extraction</li>
                    <li>Vector Similarity Analysis</li>
                    <li>Generative AI Explanations</li>
                </ul>
            </div>
        </div>
    `;
}

function updateResumeDropdown() {
    const select = document.getElementById('resumeSelect');
    if (select) {
        select.innerHTML = '<option value="">Select a resume...</option>' +
            resumes.map(resume => `<option value="${resume.id}">${resume.name}</option>`).join('');
        console.log('Resume dropdown updated');
    }
}

function findMatches() {
    console.log('FIND MATCHES FUNCTION CALLED');

    const resumeSelect = document.getElementById('resumeSelect');
    const selectedValue = resumeSelect?.value;

    if (!selectedValue) {
        showError('Please select a resume first');
        return;
    }

    const selectedResume = resumes.find(r => r.id === selectedValue);
    if (selectedResume) {
        alert(`Finding job matches for: ${selectedResume.name}\n\nThis feature would search our database for positions matching your resume skills.`);
    }
}

function loadRealJobOpportunities() {
    console.log('Loading job opportunities');

    const realJobsContainer = document.getElementById('realJobs');
    if (!realJobsContainer) {
        console.error('Real jobs container not found');
        return;
    }

    const realJobs = [
        { 
            title: "Machine Learning Engineer", 
            company: "Google", 
            location: "Mountain View, CA • Remote", 
            snippet: "Build and optimize ML models for production systems.", 
            link: "https://careers.google.com/jobs/results/?q=Machine%20Learning", 
            source: "Google Careers",
            skills: ["Python", "TensorFlow", "ML", "Cloud", "Docker"]
        },
        { 
            title: "AI Research Scientist", 
            company: "Microsoft", 
            location: "Redmond, WA • Hybrid", 
            snippet: "Research and implement cutting-edge AI algorithms.", 
            link: "https://careers.microsoft.com/professionals/us/en/search-results?keywords=AI%20Research", 
            source: "Microsoft Careers",
            skills: ["Python", "PyTorch", "Research", "NLP", "Deep Learning"]
        },
        { 
            title: "Data Scientist", 
            company: "Amazon", 
            location: "Seattle, WA • Virtual", 
            snippet: "Analyze large datasets and build predictive models.", 
            link: "https://www.amazon.jobs/en/jobs/?keywords=Data%20Scientist", 
            source: "Amazon Jobs",
            skills: ["Python", "SQL", "Machine Learning", "AWS", "Statistics"]
        }
    ];

    realJobsContainer.innerHTML = realJobs.map(job => `
        <div class="real-job-card">
            <div class="job-header">
                <div>
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company} • ${job.location}</div>
                </div>
                <a href="${job.link}" target="_blank" class="job-link">View on ${job.source}</a>
            </div>
            <div class="job-snippet">${job.snippet}</div>
            <div class="skills-list">
                ${job.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
        </div>
    `).join('');

    console.log('Job opportunities loaded');
}

function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message);
}
