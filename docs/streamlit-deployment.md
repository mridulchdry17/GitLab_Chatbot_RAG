# Streamlit Cloud Deployment Guide

## 📦 What to Push to GitHub

### ✅ **PUSH THESE:**

1. **All Source Code:**
   - `app.py`
   - `src/` directory (all Python files)
   - `requirements.txt`
   - `README.md` and documentation files
   - `.gitignore`

2. **Data File (Required):**
   - `data/gitlab_chunks.json` ✅ **MUST PUSH THIS**
   - This is the source data needed to create embeddings

### ❌ **DON'T PUSH:**

1. **Embeddings (chroma_db/):**
   - ❌ `chroma_db/` folder (too large, ~100-500 MB)
   - ✅ Will be **automatically created** on first deployment
   - ✅ **Persists** in Streamlit Cloud storage after creation

2. **Runtime Data:**
   - ❌ `data/analytics.json` (runtime analytics data)
   - ❌ `.env` file (contains API keys - use Streamlit secrets instead)

3. **Other:**
   - ❌ `venv/` (virtual environment)
   - ❌ `__pycache__/` (Python cache)

---

## 🚀 Deployment Steps

### 1. **Prepare Your Repository:**

```bash
# Make sure .gitignore is updated (already done)
# Verify gitlab_chunks.json will be tracked
git status
```

### 2. **Commit and Push:**

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 3. **Deploy to Streamlit Cloud:**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Set:
   - **Main file path:** `app.py`
   - **Python version:** 3.9+ (auto-detected)
5. Add secrets (Settings → Secrets):
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 4. **First Deployment:**

**What Happens:**
- ✅ Code deploys
- ✅ `data/gitlab_chunks.json` is available
- ⏳ **First initialization takes 5-10 minutes** (creating embeddings)
- ✅ Embeddings saved to `chroma_db/` (persists in Streamlit storage)
- ✅ **Subsequent uses are fast!** (loads from existing embeddings)

**User Experience:**
- First user sees: "Initializing system... This may take a moment"
- After 5-10 minutes: System ready ✅
- All future users: Fast initialization (< 30 seconds)

---

## 📊 Size Considerations

| Item | Size | Push? | Why |
|-----|------|-------|-----|
| `data/gitlab_chunks.json` | ~5-20 MB | ✅ Yes | Required to create embeddings |
| `chroma_db/` | ~100-500 MB | ❌ No | Too large, auto-generated |
| Source code | ~1-2 MB | ✅ Yes | Required |

**Total Push Size:** ~10-25 MB (reasonable for GitHub)

---

## ⚙️ Streamlit Cloud Configuration

### Required Secrets:

Add in Streamlit Cloud → Settings → Secrets:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### Optional Settings:

- **Python version:** 3.9+ (auto-detected)
- **Memory:** Default (1 GB) is usually enough
- **Timeout:** Default (60s) is fine for queries

---

## 🔄 How It Works on Streamlit Cloud

### First Deployment:
```
1. Code + data/gitlab_chunks.json deployed
2. User opens app
3. Auto-initialization starts
4. Loads chunks from JSON
5. Creates embeddings (5-10 min, one-time)
6. Saves to chroma_db/ (persists)
7. ✅ Ready to use!
```

### Subsequent Uses:
```
1. App loads
2. Checks if chroma_db/ exists
3. ✅ Found! Loads existing embeddings
4. ✅ Fast initialization (< 30 seconds)
5. Ready to use!
```

### If Embeddings Are Lost (rare):
- Streamlit Cloud storage is persistent
- Embeddings only regenerate if:
  - You manually delete chroma_db/
  - Streamlit Cloud resets storage (very rare)
  - You update the data file

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] `data/gitlab_chunks.json` exists and is tracked by git
- [ ] `.gitignore` allows `data/gitlab_chunks.json` but ignores `chroma_db/`
- [ ] `requirements.txt` includes all dependencies
- [ ] `GEMINI_API_KEY` is set in Streamlit secrets (NOT in code)
- [ ] All source files are committed
- [ ] README.md has deployment instructions

---

## 🐛 Troubleshooting

### Issue: "No chunks found"
**Solution:** Make sure `data/gitlab_chunks.json` is committed to git

### Issue: "GEMINI_API_KEY not found"
**Solution:** Add API key in Streamlit Cloud → Settings → Secrets

### Issue: Initialization takes too long
**Solution:** This is normal on first deployment (5-10 min). Subsequent uses are fast.

### Issue: Embeddings not persisting
**Solution:** Streamlit Cloud has persistent storage. If this happens, contact Streamlit support.

---

## 📝 Summary

**For Streamlit Cloud:**
- ✅ Push: Code + `data/gitlab_chunks.json`
- ❌ Don't push: `chroma_db/` (auto-generated)
- ⏳ First run: Creates embeddings (5-10 min)
- ✅ After that: Fast (< 30 seconds)

**This is the recommended approach!** 🚀

