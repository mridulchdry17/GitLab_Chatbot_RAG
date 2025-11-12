# Complete Project Flow: After Data Collection

## Overview

This document explains the complete flow of the GitLab Handbook Chatbot from data collection to user interaction.

---

## Phase 1: Data Collection (DONE ✅)

### Step 1: Scraping
```
python src/scraper.py
```

**What happens:**
1. Scraper visits GitLab Handbook & Direction pages
2. Recursively follows links (depth 3, max 100 pages)
3. Extracts content with metadata:
   - `source_url`
   - `section_title`
   - `start_char`
   - `end_char`
   - `content`

**Output:** `data/gitlab_chunks.json` (22,290 lines)

---

## Phase 2: Initialization (When App Starts)

### Step 2: User Clicks "Initialize System"

**Location:** `app.py` → `initialize_system()`

**Flow:**
```
1. Create VectorStore instance
   ↓
2. VectorStore.initialize()
   ↓
3. Load chunks from gitlab_chunks.json
   ↓
4. Convert to LangChain Documents (with metadata)
   ↓
5. Apply token-based chunking (~300 tokens, 50 overlap)
   ↓
6. Create embeddings (HuggingFace)
   ↓
7. Store in ChromaDB
   ↓
8. Create Chatbot instance
   ↓
9. Initialize Analytics
   ↓
10. System Ready! ✅
```

### Detailed Steps:

#### A. Vector Store Initialization (`vector_store.py`)

```python
# 1. Load chunks from JSON
chunks = load_chunks()  # Reads gitlab_chunks.json

# 2. Convert to LangChain Documents
documents = _create_langchain_documents(chunks)
# Each document has: page_content + metadata

# 3. Token-based chunking (NEW!)
documents = _split_with_metadata_preservation(documents)
# Splits large sections into ~300 token chunks
# Preserves metadata (source_url, start_char, end_char)

# 4. Create embeddings
embeddings = HuggingFaceEmbeddings('all-MiniLM-L6-v2')
# Converts text → 384-dimensional vectors

# 5. Store in ChromaDB
vector_store.add_documents(documents)
# Saves: embeddings + documents + metadata
```

**Result:** Vector database ready for semantic search

---

## Phase 3: User Interaction (When User Asks Question)

### Step 3: User Types Question

**Example:** "What is GitLab's approach to transparency?"

**Flow:**
```
User Question
    ↓
app.py (chat input)
    ↓
chatbot.generate_response(query)
    ↓
[Multiple steps happen here]
    ↓
Response displayed to user
```

### Detailed Flow Inside `generate_response()`:

#### Step 3.1: Guardrail Check
```python
check_query_appropriateness(query)
# Checks for inappropriate keywords
# Returns: (is_appropriate, message)
```

**If blocked:** Returns guardrail message, stops here

**If allowed:** Continues to next step

---

#### Step 3.2: Vector Search (RAG Retrieval)

```python
# Search for relevant chunks
search_results = vector_store.search(query, n_results=5)
```

**What happens:**
1. Convert query to embedding (same model)
2. Search ChromaDB for similar vectors
3. Returns top 5 most similar chunks
4. Each result includes:
   - `content` (text)
   - `source_url`
   - `section_title`
   - `start_char`, `end_char`
   - `distance` (similarity score)

**Result:** 5 relevant chunks from Handbook

---

#### Step 3.3: Get Source Documents (LangChain)

```python
source_documents = retriever.get_relevant_documents(query)
# Gets LangChain Document objects with metadata
```

**Purpose:** For source citations

---

#### Step 3.4: Format Context

```python
# Format documents into context string
context = format_docs(source_documents)
# Combines all chunks into one text
```

**Example output:**
```
[Source 1]
Section: Transparency
URL: https://handbook.gitlab.com/values
Content: GitLab values transparency...

[Source 2]
Section: Open Communication
URL: https://handbook.gitlab.com/values
Content: We believe in open communication...
```

---

#### Step 3.5: Build Prompt

```python
formatted_prompt = prompt_template.format(
    context=context,           # Retrieved chunks
    question=query,            # User's question
    chat_history=chat_history_str  # Previous conversation
)
```

**Prompt includes:**
- System instructions (guardrails)
- Previous conversation (if any)
- Retrieved context from Handbook
- User's question

---

#### Step 3.6: Generate Response (LLM)

```python
response = llm.invoke(formatted_prompt)
# Sends to Google Gemini API
# Returns: AI-generated answer
```

**What Gemini does:**
- Reads the context
- Understands the question
- Generates answer based on Handbook content
- Includes source citations

---

#### Step 3.7: Extract Sources & Metadata

```python
sources = extract_sources(source_documents, search_results)
# Extracts: url, section_title, relevance_score
```

**For transparency:** User can see which pages were used

---

#### Step 3.8: Calculate Confidence

```python
# Based on similarity scores
avg_distance = average of search result distances
if avg_distance < 0.3: confidence = 'high'
elif avg_distance < 0.5: confidence = 'medium'
else: confidence = 'low'
```

**Purpose:** Show user how confident the system is

---

#### Step 3.9: Track Analytics

```python
analytics.track_query(query, response)
# Saves: query, confidence, sources, timestamp
```

**Purpose:** Usage insights

---

#### Step 3.10: Return Response

```python
return {
    'response': "GitLab values transparency...",
    'sources': [...],
    'confidence': 'high',
    'context_used': True
}
```

---

## Phase 4: Display to User

### Step 4: Show in UI (`app.py`)

**What user sees:**
1. **Answer** - The generated response
2. **Sources** - Clickable links to Handbook pages
3. **Confidence Badge** - 🟢 High / 🟡 Medium / 🔴 Low
4. **Context Preview** - (Optional) Shows which sources will be used

**Features:**
- Conversation history maintained
- Can ask follow-up questions
- Export conversation
- View analytics

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. DATA COLLECTION (scraper.py)                         │
│    Scrape → Extract → Save to JSON                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. INITIALIZATION (app.py → initialize_system)          │
│    Load JSON → Token Chunking → Embeddings → ChromaDB   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. USER ASKS QUESTION                                    │
│    "What is transparency?"                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. GUARDRAIL CHECK (chatbot.py)                          │
│    Is query appropriate? → Yes/No                        │
└─────────────────────────────────────────────────────────┘
                        ↓ (if Yes)
┌─────────────────────────────────────────────────────────┐
│ 5. VECTOR SEARCH (vector_store.py)                       │
│    Query → Embedding → Search ChromaDB → Top 5 chunks   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. FORMAT CONTEXT (chatbot.py)                           │
│    Combine chunks → Format with metadata                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. BUILD PROMPT (chatbot.py)                             │
│    System prompt + Context + Question + History         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 8. LLM GENERATION (Gemini API)                            │
│    Send prompt → Generate answer                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 9. POST-PROCESSING (chatbot.py)                          │
│    Extract sources → Calculate confidence → Track        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 10. DISPLAY (app.py)                                     │
│     Show answer + sources + confidence + analytics       │
└─────────────────────────────────────────────────────────┘
```

---

## Key Components & Their Roles

### 1. Vector Store (`vector_store.py`)
- **Purpose:** Semantic search engine
- **Does:** Stores embeddings, searches for similar content
- **Uses:** LangChain ChromaDB, HuggingFace embeddings

### 2. Chatbot (`chatbot.py`)
- **Purpose:** RAG orchestration
- **Does:** Retrieves context, formats prompts, calls LLM
- **Uses:** LangChain, Google Gemini API

### 3. Analytics (`analytics.py`)
- **Purpose:** Usage tracking
- **Does:** Records queries, sources, confidence
- **Uses:** JSON file storage

### 4. App (`app.py`)
- **Purpose:** User interface
- **Does:** Displays UI, handles user input
- **Uses:** Streamlit

---

## Data Flow Summary

```
JSON File (gitlab_chunks.json)
    ↓
LangChain Documents (with metadata)
    ↓
Token-based Chunks (~300 tokens)
    ↓
Embeddings (384-dim vectors)
    ↓
ChromaDB (vector database)
    ↓
[User Query]
    ↓
Query Embedding
    ↓
Similarity Search
    ↓
Top 5 Chunks (with metadata)
    ↓
Context for LLM
    ↓
Gemini API
    ↓
Answer + Sources
    ↓
Display to User
```

---

## What Makes This RAG (Retrieval-Augmented Generation)?

1. **Retrieval:** Vector search finds relevant Handbook content
2. **Augmentation:** Context added to prompt
3. **Generation:** LLM generates answer based on retrieved context

**Result:** Answers are grounded in actual Handbook content, not just LLM knowledge!

---

## Current Status

✅ **Data Collection:** Complete (22,290 chunks)
⏭️ **Next:** Initialize system (creates embeddings)
⏭️ **Then:** Ready for questions!

