"""
GenAI Chatbot Implementation using LangChain + Google Gemini API
Includes custom guardrails, transparency features, and context management
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()


class Chatbot:
    """GenAI Chatbot with RAG capabilities using LangChain"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize LangChain LLM with Gemini
        # Note: gemini-pro is deprecated, using gemini-1.5-flash (faster) or gemini-1.5-pro (better quality)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Updated: faster and free tier friendly
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        # Custom prompt template with guardrails
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question", "chat_history"],
            template="""You are a helpful assistant that answers questions about GitLab's Handbook and Direction pages.

IMPORTANT GUIDELINES:
1. Only answer questions based on the provided context from GitLab's documentation
2. If you don't know the answer or the context doesn't contain relevant information, clearly state that
3. DO NOT make up or invent source URLs or section titles - only reference what is in the provided context
4. Be transparent about uncertainty
5. Provide comprehensive, detailed explanations that fully address the user's question
6. Structure your response clearly with proper paragraphs and organization
7. Include relevant details, examples, and key points from the context
8. If asked about topics outside GitLab documentation, politely redirect to GitLab-related questions
9. Do not include a "Sources:" section in your response - sources will be displayed separately
10. Ensure your response is helpful, informative, and easy to understand

GUARDRAILS:
- Only discuss topics related to GitLab's Handbook and Direction pages
- Do not provide information about topics not covered in the provided context
- Maintain professionalism and accuracy
- If the context doesn't fully answer the question, acknowledge what information is available and what is missing

Your goal is to help employees and aspiring employees learn about GitLab's practices, values, and direction through clear, comprehensive explanations.

Previous conversation:
{chat_history}

Context from GitLab documentation:
{context}

User question: {question}

Please provide a comprehensive, well-structured answer that fully explains the topic based on the context above. Include relevant details, examples, and key points. Make sure your explanation is clear and helpful. Do not list sources in your response."""
        )
        
        # Create retriever with custom metadata
        self.retriever = vector_store.vector_store.as_retriever(
            search_kwargs={"k": 5}
        )
        
        # Helper function to format documents
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.format_docs = format_docs
        
        # Conversation history for custom tracking
        self.conversation_history: List[Dict] = []
    
    def format_context(self, search_results: List[Dict]) -> str:
        """Format search results into context for transparency"""
        if not search_results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"[Source {i}]\n"
                f"Section: {result['section_title']}\n"
                f"URL: {result['source_url']}\n"
                f"Content: {result['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def extract_sources(self, source_documents, search_results: List[Dict] = None) -> List[Dict]:
        """Extract source information for citations with custom metadata"""
        sources = []
        seen_urls = set()
        
        # Use source_documents from LangChain if available
        if source_documents:
            for doc in source_documents:
                metadata = doc.metadata
                url = metadata.get('source_url', '')
                if url and url not in seen_urls:
                    sources.append({
                        'url': url,
                        'section_title': metadata.get('section_title', ''),
                        'start_char': metadata.get('start_char', 0),
                        'end_char': metadata.get('end_char', 0),
                        'relevance_score': None
                    })
                    seen_urls.add(url)
        
        # Also use search_results if provided (for transparency preview)
        if search_results:
            for result in search_results:
                url = result['source_url']
                if url not in seen_urls:
                    distance = result.get('distance', 0)
                    sources.append({
                        'url': url,
                        'section_title': result['section_title'],
                        'start_char': result['start_char'],
                        'end_char': result['end_char'],
                        'relevance_score': 1 - distance if distance else None
                    })
                    seen_urls.add(url)
        
        return sources
    
    def check_query_appropriateness(self, query: str) -> tuple[bool, Optional[str]]:
        """Custom Guardrail: Check if query is appropriate"""
        inappropriate_keywords = [
            'hack', 'exploit', 'bypass', 'unauthorized access',
            'personal information', 'private data', 'confidential'
        ]
        
        query_lower = query.lower()
        for keyword in inappropriate_keywords:
            if keyword in query_lower:
                return False, f"I can only help with questions about GitLab's public Handbook and Direction pages. I cannot assist with {keyword}."
        
        return True, None
    
    def generate_response(
        self, 
        query: str, 
        include_history: bool = True,
        max_context_chunks: int = 5,
        additional_context: Optional[str] = None
    ) -> Dict:
        """
        Generate response with RAG using LangChain, with custom features
        
        Returns:
            {
                'response': str,
                'sources': List[Dict],
                'confidence': str,
                'context_used': bool
            }
        """
        # Custom guardrail check (before LangChain processing)
        is_appropriate, guardrail_message = self.check_query_appropriateness(query)
        if not is_appropriate:
            return {
                'response': guardrail_message,
                'sources': [],
                'confidence': 'low',
                'context_used': False,
                'guardrail_triggered': True
            }
        
        # Get search results for transparency and source extraction
        search_results = self.vector_store.search(query, n_results=max_context_chunks)
        context_used = len(search_results) > 0
        
        try:
            # Get source documents first for metadata
            # Use invoke() for LangChain 0.1+ compatibility
            try:
                source_documents = self.retriever.invoke(query)
            except AttributeError:
                # Fallback for older LangChain versions
                source_documents = self.retriever.get_relevant_documents(query)
            
            # Format context from documents
            context = self.format_docs(source_documents)
            
            # Add additional context (e.g., from uploaded PDF) if provided
            if additional_context:
                context = f"{context}\n\n--- Additional Context (from uploaded document) ---\n{additional_context}"
            
            # Build chat history string
            chat_history_str = ""
            if include_history and self.conversation_history:
                for msg in self.conversation_history[-4:]:
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    chat_history_str += f"{role}: {msg['content']}\n"
            
            # Format prompt with context
            formatted_prompt = self.prompt_template.format(
                context=context,
                question=query,
                chat_history=chat_history_str
            )
            
            # Invoke LLM
            response = self.llm.invoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean response text - remove any LLM-generated source sections
            # LLM might add "Sources:" section even though we told it not to
            if "Sources:" in response_text or "sources:" in response_text.lower():
                # Remove everything after "Sources:" line
                lines = response_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    if line.strip().lower().startswith('sources:'):
                        break
                    cleaned_lines.append(line)
                response_text = '\n'.join(cleaned_lines).strip()
            
            # Extract sources ONLY from actual retrieved documents (not from LLM response)
            sources = self.extract_sources(source_documents, search_results)
            
            # Validate sources - ensure they have valid URLs
            validated_sources = []
            for source in sources:
                if source.get('url') and source['url'].startswith('http'):
                    validated_sources.append(source)
            sources = validated_sources
            
            # Determine confidence based on search results
            if search_results:
                avg_distance = sum(r.get('distance', 1) for r in search_results) / len(search_results)
                if avg_distance < 0.3:
                    confidence = 'high'
                elif avg_distance < 0.5:
                    confidence = 'medium'
                else:
                    confidence = 'low'
            else:
                confidence = 'low'
            
            # Update custom conversation history
            self.conversation_history.append({'role': 'user', 'content': query})
            self.conversation_history.append({'role': 'assistant', 'content': response_text})
            
            return {
                'response': response_text,
                'sources': sources,
                'confidence': confidence,
                'context_used': context_used,
                'guardrail_triggered': False
            }
            
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}. Please try again."
            return {
                'response': error_msg,
                'sources': [],
                'confidence': 'low',
                'context_used': False,
                'error': str(e)
            }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def get_context_preview(self, query: str, max_chunks: int = 3) -> List[Dict]:
        """Get preview of context that would be used (transparency feature)"""
        search_results = self.vector_store.search(query, n_results=max_chunks)
        return [
            {
                'section_title': r['section_title'],
                'url': r['source_url'],
                'preview': r['content'][:200] + '...' if len(r['content']) > 200 else r['content']
            }
            for r in search_results
        ]
