# Smart-Resume-and-Job-Matcher

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://codes-by-sethu.github.io/Smart-Resume-and-Job-Matcher/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)

An AI-powered Resume and Job Matching System that uses embeddings, semantic search, and Generative AI reasoning to match candidates' resumes with the most relevant job opportunities.

## Live Demo

**Frontend UI:** [https://codes-by-sethu.github.io/Smart-Resume-and-Job-Matcher/](https://codes-by-sethu.github.io/Smart-Resume-and-Job-Matcher/)

## 🚀 Features

- **📄 Multi-format Resume Parsing** - PDF, DOCX, TXT support
- **🧠 Semantic Matching** - Goes beyond keyword matching using SentenceTransformers
- **⚡ FAISS Vector Search** - Efficient similarity search
- **🤖 AI Explanations** - Generative AI match reasoning using Ollama
- **🌐 Dual Interfaces** - Web UI + CLI + Streamlit app
- **📊 Section-Weighted Scoring** - Skills (50%), Experience (30%), Education (20%)

## 🏗️ Project Structure

```
Smart-Resume-and-Job-Matcher/
├── ingestion/          # Resume & job parsing
├── app/               # Core AI engine (embeddings, matching)
├── docs/              # GitHub Pages frontend
├── ui/                # Streamlit interface  
├── scripts/           # CLI tools
└── data/              # Sample resumes & jobs
```

## 🛠️ Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/codes-by-sethu/Smart-Resume-and-Job-Matcher.git
cd Smart-Resume-and-Job-Matcher
pip install -r requirements.txt
```

### 2. Run CLI Demo
```bash
python scripts/demo_pipeline.py data/sample_resume.pdf
```

### 3. Run Streamlit App
```bash
streamlit run ui/streamlit_app.py
```

## 📖 Usage

### Parse Resumes
```bash
python ingestion/parsers.py data/sample_resume.pdf
```

## 🔧 Tech Stack

- **Python** - Core programming language
- **SentenceTransformers** - Semantic embeddings
- **FAISS** - Vector similarity search
- **Ollama** - AI explanations
- **Streamlit** - Web interface
- **pdfplumber/python-docx** - Document parsing

## 📄 Supported Formats

- 📄 PDF files
- 📝 DOCX documents  
- 📃 Text files

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Now your project has complete documentation! 🎉
