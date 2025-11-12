"""
Vector Store Management using LangChain + ChromaDB
Handles embeddings, token-based chunking, and similarity search for RAG
Preserves custom metadata: source_url, section_title, start_char, end_char
"""

import json
import os
import time
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import tiktoken

# Disable torch.compile to avoid compatibility issues with PyTorch 2.0.1+cpu
os.environ['TORCH_COMPILE_DISABLE'] = '1'


class VectorStore:
    """Manages vector embeddings and similarity search using LangChain"""
    
    def __init__(self, data_dir: str = 'data', persist_dir: str = 'chroma_db', 
                 chunk_size: int = 300, chunk_overlap: int = 50):
        self.data_dir = data_dir
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize embedding model
        # Using BGE-small-en-v1.5: 512 token limit, 384 dimensions, faster for real-time queries
        # CPU-only mode (no GPU needed)
        print("📦 Loading embedding model (BGE-small-en-v1.5) on CPU...")
        start_time = time.time()
        self.embedding_model = HuggingFaceEmbeddings(
            model_name='BAAI/bge-small-en-v1.5',
            model_kwargs={
                'device': 'cpu',  # Force CPU mode (no GPU needed)
                'trust_remote_code': False  # Disable remote code execution
            },
            encode_kwargs={
                'normalize_embeddings': True  # Normalize for better similarity
            }
        )
        load_time = time.time() - start_time
        print(f"✅ Embedding model loaded successfully! (took {load_time:.2f}s)")
        print(f"   Model: BGE-small-en-v1.5 | Dimensions: 384 | Context: 512 tokens")
        
        # Initialize text splitter for token-based chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize ChromaDB with LangChain
        self.vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embedding_model,
            collection_name="gitlab_handbook"
        )
        self._collection = self.vector_store._collection  # For backward compatibility
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    
    def load_chunks(self, file_path: Optional[str] = None) -> List[Dict]:
        """Load chunks from JSON file"""
        if file_path is None:
            file_path = os.path.join(self.data_dir, 'gitlab_chunks.json')
        
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_langchain_documents(self, chunks: List[Dict]) -> List[Document]:
        """Convert custom chunks to LangChain Documents with metadata"""
        documents = []
        
        for chunk in chunks:
            # Create document with custom metadata
            doc = Document(
                page_content=chunk['content'],
                metadata={
                    'source_url': chunk['source_url'],
                    'section_title': chunk['section_title'],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char'],
                    'original_content': chunk['content']  # Keep original for reference
                }
            )
            documents.append(doc)
        
        return documents
    
    def _split_with_metadata_preservation(self, documents: List[Document]) -> List[Document]:
        """Split documents while preserving and updating metadata"""
        split_docs = []
        
        for doc in documents:
            # Split the content
            splits = self.text_splitter.split_text(doc.page_content)
            
            # Calculate character offsets for each split
            current_char = doc.metadata['start_char']
            
            for i, split_text in enumerate(splits):
                split_length = len(split_text)
                split_start = current_char
                split_end = current_char + split_length
                
                # Create new document with updated metadata
                split_doc = Document(
                    page_content=split_text,
                    metadata={
                        'source_url': doc.metadata['source_url'],
                        'section_title': doc.metadata['section_title'],
                        'start_char': split_start,
                        'end_char': split_end,
                        'chunk_index': i,
                        'total_chunks': len(splits),
                        'original_start': doc.metadata['start_char'],
                        'original_end': doc.metadata['end_char']
                    }
                )
                split_docs.append(split_doc)
                
                # Update for next split (account for overlap)
                overlap_chars = self.text_splitter._chunk_overlap
                current_char = split_end - overlap_chars
        
        return split_docs
    
    def add_chunks(self, chunks: List[Dict], apply_token_chunking: bool = True):
        """Add chunks to vector store with optional token-based chunking"""
        if not chunks:
            print("⚠️  No chunks to add")
            return
        
        start_time = time.time()
        print(f"\n📊 Processing {len(chunks):,} chunks...")
        
        # Convert to LangChain documents
        print("   Converting to LangChain documents...")
        documents = self._create_langchain_documents(chunks)
        
        # Apply token-based chunking if requested
        if apply_token_chunking:
            print("   ✂️  Applying token-based chunking (~300 tokens with 50 overlap)...")
            chunk_start = time.time()
            documents = self._split_with_metadata_preservation(documents)
            chunk_time = time.time() - chunk_start
            print(f"   ✅ Split into {len(documents):,} token-based chunks (took {chunk_time:.2f}s)")
        else:
            print(f"   ℹ️  Using original chunks (no splitting)")
        
        # Check existing documents
        try:
            existing_count = self.vector_store._collection.count()
        except:
            existing_count = 0
        
        # Skip embedding creation if embeddings already exist
        if existing_count > 0:
            print(f"   ✅ Found {existing_count:,} existing documents in vector store")
            print(f"   ⏭️  Skipping embedding creation (embeddings already exist)")
            print(f"   💡 To recreate embeddings, delete the 'chroma_db' folder and reinitialize")
            total_time = time.time() - start_time
            print(f"\n✅ Using existing embeddings!")
            print(f"   📈 Total documents in vector store: {existing_count:,}")
            print(f"   ⏱️  Total time: {total_time:.2f}s (no embedding needed)\n")
            return
        
        # Add to vector store with progress logging (only if no existing embeddings)
        print(f"\n🔢 Creating embeddings for {len(documents):,} documents...")
        print("   (This may take a few minutes on CPU - please wait...)")
        embed_start = time.time()
        
        # Process in batches for progress updates
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            self.vector_store.add_documents(batch)
            
            # Progress update every batch
            if batch_num % 10 == 0 or batch_num == total_batches:
                elapsed = time.time() - embed_start
                rate = batch_num / elapsed if elapsed > 0 else 0
                remaining = (total_batches - batch_num) / rate if rate > 0 else 0
                print(f"   ⏳ Progress: {batch_num:,}/{total_batches:,} batches "
                      f"({batch_num * batch_size:,}/{len(documents):,} docs) | "
                      f"ETA: {remaining/60:.1f}min")
        
        # Persist to disk (ChromaDB with persist_directory auto-persists)
        print("   💾 Saving embeddings to disk...")
        # Note: With persist_directory set, ChromaDB auto-persists
        # Explicit persist() may not be available in newer LangChain versions
        try:
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
        except AttributeError:
            # Auto-persist is handled by persist_directory parameter
            pass
        
        total_time = time.time() - start_time
        embed_time = time.time() - embed_start
        final_count = self.vector_store._collection.count()
        
        print(f"\n✅ Successfully processed embeddings!")
        print(f"   📈 Total documents in vector store: {final_count:,}")
        print(f"   ⏱️  Total time: {total_time/60:.2f}min (embedding: {embed_time/60:.2f}min)")
        print(f"   🚀 Average speed: {len(documents)/embed_time:.1f} docs/sec\n")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar chunks with custom metadata"""
        try:
            count = self.vector_store._collection.count()
        except:
            count = 0
        if count == 0:
            return []
        
        # Use LangChain's similarity search
        results = self.vector_store.similarity_search_with_score(
            query, 
            k=n_results
        )
        
        # Format results with custom metadata
        formatted_results = []
        for doc, score in results:
            metadata = doc.metadata
            formatted_results.append({
                'content': doc.page_content,
                'source_url': metadata.get('source_url', ''),
                'section_title': metadata.get('section_title', ''),
                'start_char': int(metadata.get('start_char', 0)),
                'end_char': int(metadata.get('end_char', 0)),
                'distance': float(score)  # LangChain returns distance as score
            })
        
        return formatted_results
    
    def initialize(self, apply_token_chunking: bool = True):
        """Initialize vector store with data"""
        print("\n" + "="*60)
        print("🚀 INITIALIZING VECTOR STORE")
        print("="*60)
        chunks = self.load_chunks()
        if chunks:
            print(f"📁 Loaded {len(chunks):,} chunks from JSON file")
            self.add_chunks(chunks, apply_token_chunking=apply_token_chunking)
            print("="*60)
            print("✅ VECTOR STORE INITIALIZATION COMPLETE!")
            print("="*60 + "\n")
        else:
            print("⚠️  No chunks found. Please run scraper.py first.")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        try:
            count = self.vector_store._collection.count()
        except:
            count = 0
        return {
            'total_chunks': count,
            'collection_name': 'gitlab_handbook'
        }
