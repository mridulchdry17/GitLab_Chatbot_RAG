# Data Flow Explanation: Why Chunking Matters for RAG

## Complete Data Flow

### Step 1: Website (GitLab Handbook)
```
https://handbook.gitlab.com/handbook/values/
```
**What we get:** Full HTML page with all content (could be 5000+ words)

---

### Step 2: Scraper (`scraper.py`)
**What happens:** Extracts content and splits by sections

**Example output (saved to `gitlab_chunks.json`):**
```json
[
  {
    "source_url": "https://handbook.gitlab.com/handbook/values/",
    "section_title": "Transparency",
    "start_char": 0,
    "end_char": 2500,
    "content": "GitLab values transparency. We believe in open communication... [2500 characters of text]"
  },
  {
    "source_url": "https://handbook.gitlab.com/handbook/values/",
    "section_title": "Collaboration",
    "start_char": 2500,
    "end_char": 4800,
    "content": "Collaboration is key to our success. We work together... [2300 characters of text]"
  }
]
```

**Problem:** Each chunk might be 2000-5000 characters (400-1000 tokens)
- Too large for LLM context windows
- Less precise retrieval
- Wastes tokens

---

### Step 3: Vector Store (`vector_store.py` - CURRENT)
**What happens:** Loads chunks from JSON → Creates embeddings → Stores in ChromaDB

**Current flow:**
```python
chunks = load_chunks()  # Load from JSON (large sections)
embeddings = encode(chunks)  # Create embeddings for large chunks
chromadb.add(chunks)  # Store large chunks
```

**When user asks:** "What is GitLab's approach to transparency?"
- Vector search finds the "Transparency" section (2500 chars)
- Sends entire 2500-char chunk to LLM
- LLM gets too much context, less focused

---

### Step 4: RAG Search (When User Asks Question)
**What happens:**
1. User: "What is transparency?"
2. Vector search finds relevant chunks
3. Returns top 5 chunks (could be 10,000+ tokens total)
4. LLM receives all this context
5. LLM generates answer

**Problem with large chunks:**
- ❌ Less precise: Gets entire section when only part is relevant
- ❌ Wastes tokens: Sends 2000 chars when 300 would work
- ❌ Slower: More tokens = slower LLM response
- ❌ Less accurate: Harder to find exact relevant info

---

## Why Token-Based Chunking (~300 tokens)?

### Better RAG Performance:

**With Large Chunks (Current):**
```
User asks: "What is transparency?"
→ Finds: "Transparency" section (2500 chars = ~500 tokens)
→ LLM gets: Entire section about transparency, values, examples, etc.
→ Response: Generic, less focused
```

**With Small Chunks (~300 tokens):**
```
User asks: "What is transparency?"
→ Finds: Specific chunk about transparency definition (300 tokens)
→ LLM gets: Only relevant part
→ Response: Precise, focused answer
```

### Benefits:
1. **Better Retrieval**: Smaller chunks = more precise matching
2. **Faster**: Less tokens to process
3. **More Context**: Can fit more diverse chunks in same token budget
4. **Better Citations**: Know exactly which part of document was used

---

## Where Should Chunking Happen?

### Option A: In Scraper (Current - Section-based)
```
Website → Scraper (section chunks) → JSON → Vector Store → DB
```
- ✅ Simple
- ❌ Can't change chunking strategy without re-scraping
- ❌ Large chunks stored

### Option B: In Vector Store (Recommended - Token-based)
```
Website → Scraper (full sections) → JSON → Vector Store (token chunks) → DB
```
- ✅ Flexible: Can experiment with chunk sizes
- ✅ Better for RAG: Smaller, focused chunks
- ✅ Can re-chunk without re-scraping
- ✅ Store full sections in JSON for reference

---

## Example: What Data Looks Like

### In JSON (After Scraping):
```json
{
  "source_url": "https://handbook.gitlab.com/values",
  "section_title": "Transparency",
  "start_char": 0,
  "end_char": 2500,
  "content": "GitLab values transparency. We believe in open communication and sharing information openly. This means we share our roadmap publicly, discuss our challenges openly, and maintain transparency in our decision-making processes. We also believe that transparency builds trust with our team members and customers..."
}
```
**Size:** ~2500 characters = ~500 tokens (TOO LARGE for RAG)

### After Token-Based Chunking (In Vector Store):
```json
[
  {
    "source_url": "https://handbook.gitlab.com/values",
    "section_title": "Transparency",
    "start_char": 0,
    "end_char": 1200,
    "content": "GitLab values transparency. We believe in open communication and sharing information openly. This means we share our roadmap publicly, discuss our challenges openly...",
    "token_count": 300
  },
  {
    "source_url": "https://handbook.gitlab.com/values",
    "section_title": "Transparency",
    "start_char": 1100,  // 100 token overlap
    "end_char": 2300,
    "content": "...and maintain transparency in our decision-making processes. We also believe that transparency builds trust with our team members and customers...",
    "token_count": 300
  }
]
```
**Size:** 2 chunks of ~300 tokens each (BETTER for RAG)

---

## Summary

**Why chunking?**
- RAG works better with smaller, focused chunks
- ~300 tokens is optimal for retrieval and LLM context
- Overlap (50-100 tokens) preserves context between chunks

**Where to chunk?**
- **Scraper**: Extract full sections (preserve structure)
- **Vector Store**: Split into ~300 token chunks (optimize for RAG)

**Data flow:**
1. Website → Large HTML pages
2. Scraper → Full sections (save to JSON)
3. Vector Store → Token-based chunks (store in DB)
4. RAG → Retrieve small, relevant chunks
5. LLM → Get precise, focused answers

