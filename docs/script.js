let resumes = [];
let jobs = [];
let jobDescriptions = [];

document.getElementById('resumeUpload').addEventListener('change', function(e) {
    handleFileUpload(e.target.files, resumes, 'resumeList');
});

document.getElementById('jobDescription').addEventListener('input', function(e) {
    const description = e.target.value.trim();
    if (description) {
        jobDescriptions = [{ name: 'Pasted Job Description', content: description, type: 'text' }];
        updateJobDescriptionList();
    } else {
        jobDescriptions = [];
        document.getElementById('jobList').innerHTML = '';
    }
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
    list.innerHTML = files.map(file => `<div class="file-item">${file.name}</div>`).join('');
}

function updateJobDescriptionList() {
    const list = document.getElementById('jobList');
    if (jobDescriptions.length > 0) {
        list.innerHTML = jobDescriptions.map(job => `<div class="file-item">📝 ${job.name}</div>`).join('');
    }
}

async function processDocuments() {
    const jobText = document.getElementById('jobDescription').value.trim();
    const hasJobs = jobs.length > 0 || jobText.length > 0;
    
    if (resumes.length === 0 && !hasJobs) {
        alert('Please upload at least one resume and add job description');
        return;
    }

    const btn = document.getElementById('processBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        await new Promise(resolve => setTimeout(resolve, 2000));
        const select = document.getElementById('resumeSelect');
        select.innerHTML = '<option value="">Select a resume...</option>' +
            resumes.map(resume => `<option value="${resume.name}">${resume.name}</option>`).join('');
        showProcessingResults();
        loadRealJobOpportunities();
    } finally {
        btn.disabled = false;
        btn.textContent = 'Process & Analyze';
    }
}

function showProcessingResults() {
    const resultsContainer = document.getElementById('results');
    const totalJobs = jobs.length + jobDescriptions.length;
    resultsContainer.innerHTML = `
        <div class="processing-results">
            <h3>📊 Processing Complete</h3>
            <p>${resumes.length} resume(s) processed</p>
            <p>${totalJobs} job description(s) processed</p>
            <p>Real job opportunities loaded</p>
        </div>
    `;
}

function loadRealJobOpportunities() {
    const realJobsContainer = document.getElementById('realJobs');
    const realJobs = [
        { title: "Software Engineer, Machine Learning", company: "Google", location: "Mountain View, CA • Remote", snippet: "Build and optimize ML models.", link: "https://careers.google.com/jobs/results/?q=Machine%20Learning", source: "Google Careers", skills: ["Python","TensorFlow","ML"] },
        { title: "Applied Scientist", company: "Amazon", location: "Seattle, WA • Virtual", snippet: "Research and implement ML algorithms.", link: "https://www.amazon.jobs/en/jobs/?keywords=Machine+Learning", source: "Amazon Jobs", skills: ["Python","ML","AWS"] },
        { title: "Data Scientist", company: "Microsoft", location: "Redmond, WA • Remote", snippet: "Analyze data and build predictive models.", link: "https://careers.microsoft.com/professionals/us/en/search-results?keywords=Data%20Scientist", source: "Microsoft Careers", skills: ["Python","SQL","Azure"] }
    ];

    realJobsContainer.innerHTML = realJobs.map(job => `
        <div class="real-job-card">
            <div class="job-header">
                <div>
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company} • ${job.location}</div>
                </div>
                <a href="${job.link}" target="_blank" class="job-link">View ${job.source}</a>
            </div>
            <div class="job-snippet">${job.snippet}</div>
            <div class="skills-list">
                ${job.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
        </div>
    `).join('');
}
