# 🤖 GitLab Handbook Chatbot

<div align="center">

**An intelligent GenAI chatbot that helps employees and aspiring employees easily access information from GitLab's Handbook and Direction pages.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Deployment](#-deployment)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Deployment](#-deployment)
- [Technology Stack](#-technology-stack)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This project implements a **Retrieval-Augmented Generation (RAG)** chatbot that enables users to query GitLab's extensive Handbook and Direction documentation through natural language. Built with transparency, collaboration, and learning in mind, following GitLab's "build in public" philosophy.

### Key Highlights

- 🔍 **Intelligent RAG System**: Semantic search with vector embeddings for precise information retrieval
- 💬 **Conversational AI**: Natural language interactions with context awareness
- 📚 **Transparency First**: Source citations, context preview, and confidence indicators
- 🛡️ **Built-in Guardrails**: Safety features ensuring accurate and appropriate responses
- 📊 **Analytics Dashboard**: Track usage patterns and insights
- 🚀 **Production Ready**: Deployed on Streamlit Cloud with persistent storage

---

## ✨ Features

### Core Functionality

- **🔍 Intelligent Search**: RAG-based retrieval from GitLab's Handbook and Direction pages
- **💬 Conversational Interface**: Context-aware conversations with follow-up question support
- **📚 Source Citations**: Transparent source tracking with clickable URLs and section titles
- **🛡️ Guardrails**: Query filtering and safety checks for appropriate responses
- **📊 Analytics**: Usage tracking, confidence distribution, and popular sources
- **💡 Query Suggestions**: Pre-populated questions to help users get started
- **🔍 Context Preview**: See exactly which sources are being used (transparency feature)
- **📄 PDF Upload**: Optional secondary context from uploaded PDF documents
- **💾 Conversation Export**: Download conversation history as JSON
- **🎨 Modern UI**: Clean, intuitive interface with GitLab branding

### Unique Innovations

1. **Transparency Features**: Context preview shows sources before answering
2. **Metadata Preservation**: Full tracking of `source_url`, `section_title`, `start_char`, `end_char`
3. **Token-Based Chunking**: Optimized ~300 token chunks with overlap for better RAG performance
4. **Custom Guardrails**: Query filtering and safety checks beyond LLM defaults
5. **Analytics Dashboard**: Visual insights into usage patterns and confidence distribution

---

## 🏗️ Architecture

### RAG Pipeline

```
┌─────────────────┐
│  Web Scraping   │ → GitLab Handbook & Direction Pages
└─────────────────┘
         ↓
┌─────────────────┐
│  Data Storage   │ → JSON with metadata (source_url, section_title, etc.)
└─────────────────┘
         ↓
┌─────────────────┐
│ Token Chunking   │ → ~300 tokens per chunk with 50 token overlap
└─────────────────┘
         ↓
┌─────────────────┐
│   Embeddings    │ → BGE-small-en-v1.5 (384 dimensions)
└─────────────────┘
         ↓
┌─────────────────┐
│  Vector Store   │ → ChromaDB (local persistence)
└─────────────────┘
         ↓
┌─────────────────┐
│  RAG Retrieval  │ → Semantic search for relevant chunks
└─────────────────┘
         ↓
┌─────────────────┐
│  LLM Generation │ → Google Gemini 2.5 Flash
└─────────────────┘
         ↓
┌─────────────────┐
│  Response +     │ → Answer with sources, confidence, metadata
│  Transparency   │
└─────────────────┘
```

### Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **LLM**: Google Gemini 2.5 Flash API
- **Vector Database**: ChromaDB (local persistence)
- **Embeddings**: BAAI/bge-small-en-v1.5 (384 dimensions, 512 token context)
- **Framework**: LangChain & LangGraph for RAG infrastructure
- **Scraping**: BeautifulSoup4 with recursive link following
- **Chunking**: Token-based using `tiktoken` and `RecursiveCharacterTextSplitter`

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google AI Studio API key ([Get one here](https://aistudio.google.com) - Free tier: 1,500 calls/day)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jovean_intern
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

5. **Scrape GitLab data** (first time only)
   ```bash
   python src/scraper.py
   ```
   This recursively crawls GitLab's Handbook and Direction pages and saves structured data to `data/gitlab_chunks.json`.

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will open in your browser at `http://localhost:8501`.

### First-Time Setup

1. Click **"🔄 Re-initialize System"** in the sidebar (first time only)
2. Wait for initialization (creates embeddings from scraped data - takes 5-10 minutes)
3. Start asking questions!

**Note**: Initialization only happens once. Subsequent app starts are fast (< 30 seconds).

---

## 📁 Project Structure

```
jovean_intern/
├── src/                          # Source code
│   ├── scraper.py               # Web scraper with recursive crawling
│   ├── vector_store.py          # Vector database & embeddings (LangChain + ChromaDB)
│   ├── chatbot.py               # RAG chatbot implementation (LangChain + Gemini)
│   ├── analytics.py             # Usage analytics and insights
│   ├── query_suggestions.py     # Query suggestion system
│   └── utils.py                 # Utility functions
├── docs/                         # Documentation
│   ├── data-flow.md             # Data flow explanation
│   ├── project-flow.md          # Complete project workflow
│   ├── deployment.md            # General deployment guide
│   ├── streamlit-deployment.md  # Streamlit Cloud specific guide
│   └── langchain-migration.md   # LangChain integration details
├── data/                         # Data storage
│   └── gitlab_chunks.json       # Scraped data (committed to git)
├── chroma_db/                    # Vector database (auto-generated, gitignored)
├── app.py                        # Main Streamlit application
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── README.md                     # This file
├── QUICK_START.md               # Quick setup guide
├── FEATURES.md                   # Feature list
└── PROJECT_WRITEUP.md           # Detailed project documentation
```

---

## 📚 Documentation

### Main Documentation

- **[Features List](FEATURES.md)** - Complete feature overview

### Technical Documentation

- **[Data Flow Explanation](docs/data-flow.md)** - How data flows from scraping to RAG
- **[Project Flow](docs/project-flow.md)** - Complete workflow from data collection to user interaction
- **[LangChain Migration](docs/langchain-migration.md)** - Details about LangChain integration

### Deployment Documentation

- **[Deployment Guide](docs/deployment.md)** - General deployment considerations
- **[Streamlit Deployment](docs/streamlit-deployment.md)** - Step-by-step Streamlit Cloud deployment

### Key Concepts

#### Data Flow
1. **Scraping**: Recursively crawl GitLab Handbook & Direction pages
2. **Storage**: Save structured data with metadata to JSON
3. **Chunking**: Token-based chunking (~300 tokens) for optimal RAG
4. **Embeddings**: Convert chunks to 384-dimensional vectors
5. **Vector Store**: Store in ChromaDB for semantic search
6. **Retrieval**: Find relevant chunks using similarity search
7. **Generation**: LLM generates answer from retrieved context

#### RAG Architecture
- **Retrieval**: Semantic search finds relevant Handbook content
- **Augmentation**: Context added to LLM prompt
- **Generation**: LLM generates answer grounded in Handbook content

---

## 🚢 Deployment

### Streamlit Cloud (Recommended)

1. **Push to GitHub**
   - Ensure `data/gitlab_chunks.json` is committed
   - Push code to your GitHub repository

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file: `app.py`
   - Add `GEMINI_API_KEY` in Secrets

3. **First Deployment**
   - First initialization takes 5-10 minutes (creates embeddings)
   - Embeddings persist in Streamlit Cloud storage
   - Subsequent uses are fast (< 30 seconds)

**Detailed Guide**: See [docs/streamlit-deployment.md](docs/streamlit-deployment.md)

### Other Platforms

- **Hugging Face Spaces**: Similar to Streamlit Cloud
- **Local Deployment**: Run `streamlit run app.py`
- **Vercel/Serverless**: Not recommended (no persistent storage)

---

## 🛠️ Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit 1.28.0 | Web interface |
| **LLM** | Google Gemini 2.5 Flash | Response generation |
| **Vector DB** | ChromaDB 0.4.15 | Semantic search storage |
| **Embeddings** | BAAI/bge-small-en-v1.5 | Text-to-vector conversion |
| **Framework** | LangChain 0.1+ | RAG infrastructure |
| **Scraping** | BeautifulSoup4 | Web content extraction |
| **Chunking** | tiktoken + RecursiveCharacterTextSplitter | Token-based text splitting |

### Key Libraries

- `langchain-google-genai` - Google Gemini integration
- `langchain-chroma` - ChromaDB integration
- `sentence-transformers` - Embedding models
- `PyPDF2` - PDF document processing (optional feature)

---

## 🎯 Use Cases

- **For Employees**: Quickly find information from GitLab's Handbook
- **For Candidates**: Learn about GitLab's culture, values, and practices
- **For Researchers**: Explore GitLab's documentation through natural language
- **For Teams**: Share knowledge and answer questions about GitLab practices

---

## 🔧 Configuration

### Scraper Configuration

Edit `src/scraper.py` to customize:
- `max_depth`: Link crawling depth (default: 3)
- `max_pages`: Maximum pages per domain (default: 100)

### Vector Store Configuration

Edit `src/vector_store.py` to customize:
- `chunk_size`: Tokens per chunk (default: 300)
- `chunk_overlap`: Overlap between chunks (default: 50)

### Chatbot Configuration

Edit `src/chatbot.py` to customize:
- `max_context_chunks`: Number of chunks to retrieve (default: 5)
- `temperature`: LLM creativity (default: 0.7)

---

## 🤝 Contributing

This project follows GitLab's "build in public" philosophy. Contributions and feedback are welcome!

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 style guide
- Use type hints
- Add docstrings to functions and classes
- Write clear, descriptive commit messages

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **GitLab** for their open Handbook and "build in public" philosophy
- **LangChain** for the excellent RAG framework
- **Streamlit** for the amazing web framework
- **Google** for the Gemini API

---

## 📧 Contact

Built with ❤️ by **mridul**

Powered by **LangChain** & **Google Gemini AI**

---

<div align="center">

**⭐ If you find this project helpful, please consider giving it a star! ⭐**

</div>

