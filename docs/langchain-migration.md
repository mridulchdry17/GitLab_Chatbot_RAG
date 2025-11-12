# LangChain & LangGraph Integration

## What Changed

### ✅ Added LangChain & LangGraph
- Integrated LangChain for RAG infrastructure
- Added LangGraph support (ready for future agent workflows)
- Cleaner, more maintainable code

### ✅ Preserved All Custom Features

#### 1. Custom Metadata Tracking
- ✅ `source_url` - Preserved
- ✅ `section_title` - Preserved  
- ✅ `start_char` - Preserved and updated for token chunks
- ✅ `end_char` - Preserved and updated for token chunks

#### 2. Custom Transparency Features
- ✅ Context preview - Still works
- ✅ Source citations - Enhanced with LangChain source documents
- ✅ Confidence indicators - Preserved

#### 3. Custom Guardrails
- ✅ Query filtering - Still active
- ✅ Safety checks - Preserved
- ✅ Custom prompt templates - Enhanced

### ✅ New Features Added

#### Token-Based Chunking
- Uses LangChain's `RecursiveCharacterTextSplitter`
- ~300 tokens per chunk (configurable)
- 50 token overlap (configurable)
- Preserves metadata across splits

#### LangChain RAG Chain
- Uses `RetrievalQA` chain for better RAG
- Automatic context retrieval
- Better prompt management
- Conversation memory integration

## Code Changes

### `src/vector_store.py`
**Before:** Manual ChromaDB + Sentence Transformers
**After:** LangChain ChromaDB + HuggingFace Embeddings + Text Splitter

**Key Changes:**
- Uses `langchain_chroma.Chroma` instead of raw ChromaDB
- Uses `RecursiveCharacterTextSplitter` for token-based chunking
- Preserves all custom metadata in Document objects
- Cleaner API with LangChain abstractions

### `src/chatbot.py`
**Before:** Manual prompt building + Gemini API
**After:** LangChain RAG Chain + Custom guardrails

**Key Changes:**
- Uses `RetrievalQA` chain for RAG
- Uses `ChatGoogleGenerativeAI` (LangChain wrapper)
- Custom guardrails still applied before LangChain
- Custom transparency features preserved
- Better conversation memory management

## Benefits

1. **Cleaner Code:** Less boilerplate, more maintainable
2. **Token Chunking:** Better RAG performance with ~300 token chunks
3. **Industry Standard:** Using LangChain (industry standard framework)
4. **Future Ready:** Easy to add agents, tools, etc. with LangGraph
5. **Custom Features:** All custom features preserved and enhanced

## Migration Notes

### For Existing Data
- Old ChromaDB data will be regenerated with token-based chunks
- Metadata is preserved and enhanced
- First initialization will take longer (chunking + embedding)

### For New Deployments
- Works exactly the same
- Just install new requirements: `pip install -r requirements.txt`
- Initialize as before

## Usage

Everything works the same from user perspective:
```python
# Initialize (same as before)
vector_store = VectorStore()
vector_store.initialize()  # Now with token chunking!

# Chatbot (same as before)
chatbot = Chatbot(vector_store)
response = chatbot.generate_response("What is transparency?")
# Still has all custom features!
```

## Next Steps (Optional)

### With LangGraph (for agents):
```python
from langgraph.graph import StateGraph

# Can add agent workflows
# Multi-step reasoning
# Tool calling
# Complex decision trees
```

### With LangChain Tools:
```python
from langchain.tools import Tool

# Can add web search
# Can add calculator
# Can add custom tools
```

## Summary

✅ **Cleaner:** Less code, more maintainable
✅ **Better:** Token-based chunking for better RAG
✅ **Standard:** Using industry-standard LangChain
✅ **Preserved:** All custom features intact
✅ **Enhanced:** Better RAG chain, better memory management

