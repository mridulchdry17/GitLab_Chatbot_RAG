# Deployment Guide: Embeddings & ChromaDB

## ⚠️ Current Deployment Issue

### Problem:
- `chroma_db/` folder is in `.gitignore` (not committed to git)
- `data/` folder is in `.gitignore` (not committed to git)
- When you deploy, these folders **won't exist**

### What Happens on Deployment:

#### First Deployment:
```
1. Code deployed (no chroma_db/, no data/)
2. User opens app
3. Clicks "Initialize System"
4. ❌ ERROR: No gitlab_chunks.json found
5. ❌ Can't create embeddings (no data to embed)
```

#### If Data Files Were Included:
```
1. Code + data deployed
2. User opens app
3. Clicks "Initialize System"
4. ✅ Loads chunks from JSON
5. ✅ Creates embeddings (takes 5-10 minutes)
6. ✅ Saves to chroma_db/ (in cloud storage)
7. ✅ Works after that
```

---

## Deployment Platform Behavior

### 1. Streamlit Community Cloud

**Storage:**
- ✅ **Persistent storage** between sessions
- ✅ `chroma_db/` folder persists after creation
- ✅ Embeddings saved permanently
- ⚠️ **BUT**: Need to include `data/gitlab_chunks.json` in git

**What Happens:**
```
First Deploy:
- No chroma_db/ exists
- No data/ exists (if gitignored)
- App fails to initialize

After Fix (include data/):
- First user: Creates embeddings (slow, 5-10 min)
- Embeddings saved to chroma_db/
- Next users: Fast (loads from chroma_db/)
- Works perfectly!
```

**Solution:**
- Include `data/gitlab_chunks.json` in git (remove from .gitignore)
- OR: Pre-create embeddings locally and commit `chroma_db/`

---

### 2. Hugging Face Spaces

**Storage:**
- ✅ **Persistent storage** (similar to Streamlit)
- ✅ `chroma_db/` persists
- ⚠️ Same issue: Need data files

**What Happens:**
- Same as Streamlit Cloud
- First initialization creates embeddings
- Subsequent uses are fast

---

### 3. Vercel (Serverless)

**Storage:**
- ❌ **NO persistent storage** (ephemeral)
- ❌ `chroma_db/` gets deleted after each request
- ❌ **Won't work** with current setup

**What Happens:**
```
Every Request:
- chroma_db/ doesn't exist
- Tries to create embeddings
- Takes too long (timeout)
- ❌ Fails
```

**Solution:**
- Use external vector DB (Pinecone, Weaviate)
- OR: Pre-compute embeddings and use in-memory DB
- OR: Don't use Vercel for this project

---

## Solutions for Deployment

### Solution 1: Include Data Files in Git (Recommended for Streamlit/HF)

**Steps:**
1. Remove `data/` from `.gitignore`
2. Commit `gitlab_chunks.json` to git
3. Deploy
4. First initialization creates embeddings
5. Works after that

**Pros:**
- Simple
- Works on Streamlit/HF
- Embeddings created once

**Cons:**
- Large JSON file in git (~22K lines)
- Slower first initialization

---

### Solution 2: Pre-create Embeddings Locally

**Steps:**
1. Run locally: Create embeddings
2. Remove `chroma_db/` from `.gitignore`
3. Commit `chroma_db/` folder to git
4. Deploy (embeddings already exist)
5. Fast initialization

**Pros:**
- Fast deployment
- No embedding creation needed

**Cons:**
- Large folder in git
- Need to update if data changes

---

### Solution 3: Use External Vector DB (Best for Production)

**Options:**
- Pinecone (free tier available)
- Weaviate Cloud
- Qdrant Cloud

**Steps:**
1. Create account on vector DB service
2. Modify `vector_store.py` to use external DB
3. Upload embeddings once
4. Deploy (no local storage needed)

**Pros:**
- Works on any platform
- Scalable
- No local storage issues

**Cons:**
- External dependency
- May have costs at scale

---

## Recommended Approach

### For Interview/Project Submission:

**Option A: Streamlit Cloud (Easiest)**
1. Remove `data/` from `.gitignore`
2. Commit `gitlab_chunks.json`
3. Deploy to Streamlit Cloud
4. First user creates embeddings (one-time, 5-10 min)
5. Works perfectly after that

**Option B: Pre-create Embeddings**
1. Run locally to create embeddings
2. Remove `chroma_db/` from `.gitignore` (temporarily)
3. Commit `chroma_db/` folder
4. Deploy (embeddings ready)
5. Fast for all users

---

## Current Code Behavior on Deployment

### What Works:
- ✅ Code deployment
- ✅ App starts
- ✅ UI loads

### What Doesn't Work (Current):
- ❌ Initialization fails (no data file)
- ❌ Can't create embeddings
- ❌ Chatbot won't work

### What Will Work (After Fix):
- ✅ Load data from JSON
- ✅ Create embeddings (first time only)
- ✅ Save to chroma_db/ (persists)
- ✅ Fast subsequent uses
- ✅ Works exactly like local

---

## Summary

| Platform | Persistent Storage? | Current Status | Solution Needed |
|----------|-------------------|----------------|-----------------|
| **Streamlit Cloud** | ✅ Yes | ❌ Fails (no data) | Include data/ in git |
| **Hugging Face** | ✅ Yes | ❌ Fails (no data) | Include data/ in git |
| **Vercel** | ❌ No | ❌ Won't work | Use external DB |
| **Local** | ✅ Yes | ✅ Works | None |

**Answer:** Yes, it will work similarly **IF** you include the data files in your deployment. Otherwise, embeddings will be recreated on first use (which is fine, just slower).

