"""
Streamlit Application for GitLab Handbook Chatbot
Main entry point for the web interface
"""

import streamlit as st
import os
import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from chatbot import Chatbot
from vector_store import VectorStore
from utils import format_source_citation, get_confidence_badge, save_conversation_history, load_conversation_history
from analytics import Analytics
from query_suggestions import QuerySuggestions

# Page configuration
st.set_page_config(
    page_title="GitLab Handbook Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    /* Main Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FC6D26;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    
    /* Chat Messages */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #E8F4F8;
        border-left: 4px solid #FC6D26;
    }
    .assistant-message {
        background-color: #F5F5F5;
        border-left: 4px solid #4CAF50;
    }
    
    /* Links */
    .source-link {
        color: #FC6D26;
        text-decoration: none;
        font-weight: 500;
    }
    .source-link:hover {
        text-decoration: underline;
        color: #E55A1A;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background-color: #FC6D26;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #E55A1A;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(252, 109, 38, 0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #FC6D26;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #333;
    }
    
    /* Confidence Badges */
    .confidence-high {
        color: #4CAF50;
        font-weight: 600;
    }
    .confidence-medium {
        color: #FF9800;
        font-weight: 600;
    }
    .confidence-low {
        color: #F44336;
        font-weight: 600;
    }
    
    /* Status Indicators */
    .status-ready {
        padding: 0.5rem;
        background-color: #E8F5E9;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    .status-warning {
        padding: 0.5rem;
        background-color: #FFF3E0;
        border-radius: 0.5rem;
        border-left: 4px solid #FF9800;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #FC6D26;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #E55A1A;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: #666;
    }
    .example-question {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
    }
    .example-question:hover {
        background: #E8F4F8;
        border-color: #FC6D26;
        transform: translateX(5px);
    }
    
    /* Feedback Buttons */
    .feedback-container {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        align-items: center;
    }
    .feedback-btn {
        background: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 0.25rem 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .feedback-btn:hover {
        background: #e0e0e0;
    }
    .feedback-btn.active {
        background: #4CAF50;
        color: white;
        border-color: #4CAF50;
    }
    .feedback-btn.active.negative {
        background: #F44336;
        border-color: #F44336;
    }
    
    /* Performance Indicator */
    .performance-badge {
        display: inline-block;
        background: #E8F5E9;
        color: #2E7D32;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'analytics' not in st.session_state:
    st.session_state.analytics = None
if 'show_analytics' not in st.session_state:
    st.session_state.show_analytics = False
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = {}
if 'uploaded_pdf_text' not in st.session_state:
    st.session_state.uploaded_pdf_text = None
if 'uploaded_pdf_name' not in st.session_state:
    st.session_state.uploaded_pdf_name = None


def initialize_system():
    """Initialize chatbot and vector store"""
    try:
        # Initialize vector store
        if st.session_state.vector_store is None:
            st.session_state.vector_store = VectorStore()
            st.session_state.vector_store.initialize()
        
        # Initialize chatbot
        if st.session_state.chatbot is None:
            st.session_state.chatbot = Chatbot(st.session_state.vector_store)
        
        # Initialize analytics
        if st.session_state.analytics is None:
            st.session_state.analytics = Analytics()
        
        st.session_state.initialized = True
        return True
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        st.info("Please make sure you have:")
        st.info("1. Set GEMINI_API_KEY in your .env file")
        st.info("2. Run scraper.py to collect data")
        st.info("3. Installed all dependencies")
        return False


# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Re-initialize button (for manual refresh if needed)
    if st.button("🔄 Re-initialize System", use_container_width=True):
        st.session_state.initialized = False
        st.session_state.chatbot = None
        st.session_state.vector_store = None
        st.rerun()  # Will trigger auto-initialization
    
    st.divider()
    
    # System status
    if st.session_state.initialized:
        st.markdown('<div class="status-ready">✅ <strong>System Ready</strong></div>', unsafe_allow_html=True)
        if st.session_state.vector_store:
            try:
                stats = st.session_state.vector_store.get_stats()
                st.metric("📊 Total Chunks", f"{stats['total_chunks']:,}")
            except Exception as e:
                st.error(f"Error getting stats: {str(e)}")
    else:
        st.markdown('<div class="status-warning">⚠️ <strong>System Not Initialized</strong></div>', unsafe_allow_html=True)
        st.info("Click 'Initialize System' to start")
    
    st.divider()
    
    # Conversation controls
    st.subheader("💬 Conversation")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.chatbot:
            st.session_state.chatbot.clear_history()
        st.rerun()
    
    # Export conversation
    if st.session_state.messages:
        conversation_json = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            label="📥 Export Conversation",
            data=conversation_json,
            file_name="conversation.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.divider()
    
    # PDF Upload (Optional Secondary Context)
    st.subheader("📄 Optional: Upload PDF")
    st.caption("Add a PDF document as additional context for your questions")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        key="pdf_uploader",
        help="Upload a PDF to provide additional context. This is optional."
    )
    
    if uploaded_file is not None:
        # Process PDF
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text() + "\n"
            
            if pdf_text.strip():
                st.session_state.uploaded_pdf_text = pdf_text
                st.session_state.uploaded_pdf_name = uploaded_file.name
                st.success(f"✅ PDF loaded: **{uploaded_file.name}** ({len(pdf_reader.pages)} pages)")
            else:
                st.warning("⚠️ Could not extract text from PDF. Please try another file.")
                st.session_state.uploaded_pdf_text = None
                st.session_state.uploaded_pdf_name = None
        except ImportError:
            st.error("❌ PyPDF2 library not installed. Please install it: `pip install PyPDF2`")
            st.session_state.uploaded_pdf_text = None
            st.session_state.uploaded_pdf_name = None
        except Exception as e:
            st.error(f"❌ Error reading PDF: {str(e)}")
            st.session_state.uploaded_pdf_text = None
            st.session_state.uploaded_pdf_name = None
    
    # Clear PDF button
    if st.session_state.uploaded_pdf_text:
        if st.button("🗑️ Clear PDF", key="clear_pdf", use_container_width=True):
            st.session_state.uploaded_pdf_text = None
            st.session_state.uploaded_pdf_name = None
            st.rerun()
    
    st.divider()
    
    # Analytics toggle
    st.subheader("📊 Analytics")
    if st.button("📈 View Insights", use_container_width=True):
        st.session_state.show_analytics = not st.session_state.show_analytics
    
    st.divider()
    
    # Dark mode toggle
    st.subheader("🎨 Appearance")
    dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.info("💡 Dark mode styling coming soon!")
    
    st.divider()
    
    # Query suggestions
    st.subheader("💡 Suggestions")
    suggestions = QuerySuggestions.get_suggestions(3)
    for idx, suggestion in enumerate(suggestions):
        # Use index to ensure unique keys
        if st.button(suggestion, key=f"suggest_{idx}", use_container_width=True):
            # Add suggestion as user message
            st.session_state.messages.append({"role": "user", "content": suggestion})
            st.rerun()
    
    st.divider()
    
    # About section
    st.subheader("ℹ️ About")
    st.markdown("""
    This chatbot helps you explore GitLab's Handbook and Direction pages.
    
    **Features:**
    - 🔍 Intelligent search
    - 📚 Source citations
    - 🛡️ Safety guardrails
    - 💾 Conversation history
    - 📊 Usage analytics
    - 💡 Query suggestions
    
    Built with transparency and learning in mind.
    """)


# Analytics panel
if st.session_state.show_analytics and st.session_state.analytics:
    with st.expander("📊 Usage Analytics", expanded=True):
        insights = st.session_state.analytics.get_insights()
        if insights.get('total_queries', 0) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Queries", insights['total_queries'])
            with col2:
                st.metric("Avg Confidence", f"{insights.get('average_confidence', 0):.2f}")
            with col3:
                st.metric("Guardrail Triggers", insights.get('guardrail_triggers', 0))
            
            if insights.get('top_sources'):
                st.subheader("Most Accessed Sources")
                for url, count in list(insights['top_sources'].items())[:5]:
                    st.markdown(f"- [{url}]({url}): {count} times")
        else:
            st.info("No analytics data yet. Start asking questions!")

# Main content
st.markdown('<div class="main-header">🤖 GitLab Handbook Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask questions about GitLab\'s Handbook and Direction pages</div>', unsafe_allow_html=True)

# Auto-initialize if not done (for seamless deployment)
if not st.session_state.initialized:
    # Clear welcome message and show initialization status
    st.info("""
    **🔄 Auto-Initializing System...**
    
    The system is automatically setting up for you. This only happens once and takes a few seconds.
    You don't need to click anything - just wait a moment!
    
    *Loading embedding model and preparing the knowledge base...*
    """)
    
    with st.spinner("🚀 Initializing system... This may take a moment on first run."):
        if initialize_system():
            st.success("✅ **System initialized successfully!** You can now start asking questions.")
            st.balloons()  # Celebration effect
            st.rerun()  # Refresh to show initialized state
        else:
            st.error("❌ **Initialization failed.** Please check the error messages above.")
            st.info("""
            **Troubleshooting:**
            1. Make sure you have set `GEMINI_API_KEY` in your `.env` file
            2. Ensure `data/gitlab_chunks.json` exists (run `python src/scraper.py` if needed)
            3. Check that all dependencies are installed
            """)
            st.stop()

# Display chat history or empty state
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        # Empty state with example questions (Product Thinking: Onboarding UX)
        st.markdown("""
        <div class="empty-state">
            <h2 style="color: #FC6D26; margin-bottom: 1rem;">👋 Welcome to GitLab Handbook Chatbot!</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem;">
                Ask me anything about GitLab's Handbook and Direction pages.<br>
                I'll help you find information quickly and accurately.
            </p>
            <h3 style="color: #333; margin-bottom: 1rem;">💡 Try asking:</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Example questions in columns
        col1, col2 = st.columns(2)
        example_questions = [
            "What is GitLab's approach to transparency?",
            "How does GitLab handle remote work?",
            "What are GitLab's core values?",
            "How does GitLab prioritize features?",
            "What is GitLab's hiring process?",
            "How does GitLab handle security?"
        ]
        
        for i, question in enumerate(example_questions):
            col = col1 if i % 2 == 0 else col2
            with col:
                if st.button(f"💬 {question}", key=f"example_{i}", use_container_width=True):
                    # Trigger response generation by setting a flag (don't add message here, let processing handle it)
                    st.session_state.pending_query = question
                    st.rerun()
    else:
        # Display existing messages
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show sources if available
                if "sources" in message and message["sources"]:
                    with st.expander("📚 Sources", expanded=False):
                        for source in message["sources"]:
                            st.markdown(f"- {format_source_citation(source)}")
                
                # Show confidence and performance if available
                if "confidence" in message:
                    confidence_badge = get_confidence_badge(message['confidence'])
                    performance_info = ""
                    if "response_time" in message:
                        performance_info = f'<span class="performance-badge">⚡ {message["response_time"]:.2f}s</span>'
                    st.caption(f"Confidence: {confidence_badge}{performance_info}", unsafe_allow_html=True)
                
                # Feedback buttons for assistant messages (Product Thinking: Feedback Loop)
                if message["role"] == "assistant" and idx > 0:
                    col1, col2, col3 = st.columns([1, 1, 10])
                    with col1:
                        feedback_key = f"feedback_up_{idx}"
                        is_up = st.session_state.feedback_data.get(feedback_key, False)
                        if st.button("👍", key=feedback_key, help="This answer was helpful"):
                            st.session_state.feedback_data[feedback_key] = not is_up
                            if not is_up:
                                st.success("Thanks for your feedback!")
                    with col2:
                        feedback_key = f"feedback_down_{idx}"
                        is_down = st.session_state.feedback_data.get(feedback_key, False)
                        if st.button("👎", key=feedback_key, help="This answer needs improvement"):
                            st.session_state.feedback_data[feedback_key] = not is_down
                            if not is_down:
                                st.info("Thanks! We'll use this to improve.")

# Always show chat input (must be called every render)
chat_input_prompt = st.chat_input("Ask a question about GitLab's Handbook or Direction pages...")

# Handle pending query from example questions OR regular chat input
prompt = None
if 'pending_query' in st.session_state and st.session_state.pending_query:
    prompt = st.session_state.pending_query
    del st.session_state.pending_query
elif chat_input_prompt:
    prompt = chat_input_prompt

# Process query if we have one
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        start_time = time.time()
        
        with st.spinner("🔍 Searching GitLab Handbook..."):
            try:
                # Show context preview (transparency feature)
                try:
                    context_preview = st.session_state.chatbot.get_context_preview(prompt)
                    if context_preview:
                        with st.expander("🔍 Context Preview (Transparency)", expanded=False):
                            st.caption("These are the sources being used to answer your question:")
                            for ctx in context_preview:
                                st.markdown(f"**{ctx['section_title']}**")
                                st.markdown(f"🔗 [{ctx['url']}]({ctx['url']})")
                                st.markdown(f"*{ctx['preview']}*")
                                st.divider()
                except Exception as e:
                    st.debug(f"Context preview error: {str(e)}")
                
                # Get additional context from uploaded PDF if available
                additional_context = None
                if st.session_state.uploaded_pdf_text:
                    # Chunk PDF text to fit within token limits
                    pdf_text = st.session_state.uploaded_pdf_text
                    # Limit PDF context to ~1000 tokens to avoid overwhelming the prompt
                    import tiktoken
                    encoding = tiktoken.get_encoding("cl100k_base")
                    pdf_tokens = encoding.encode(pdf_text)
                    if len(pdf_tokens) > 1000:
                        pdf_text = encoding.decode(pdf_tokens[:1000])
                        pdf_text += "\n\n[PDF content truncated for length...]"
                    additional_context = pdf_text
                
                response = st.session_state.chatbot.generate_response(
                    prompt, 
                    additional_context=additional_context
                )
                response_time = time.time() - start_time
                response['response_time'] = response_time
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
                response = {
                    'response': "I apologize, but I encountered an error while processing your question. Please try again or rephrase your question.",
                    'sources': [],
                    'confidence': 'low',
                    'context_used': False,
                    'error': str(e)
                }
        
        # Track in analytics
        if st.session_state.analytics:
            st.session_state.analytics.track_query(prompt, response)
        
        # Show PDF indicator if PDF was used
        if st.session_state.uploaded_pdf_text:
            st.info(f"📄 **Using additional context from:** {st.session_state.uploaded_pdf_name}")
        
        # Display response
        st.markdown(response['response'])
        
        # Display sources
        if response['sources']:
            with st.expander("📚 Sources", expanded=True):
                for source in response['sources']:
                    st.markdown(f"- {format_source_citation(source)}")
                    if source.get('relevance_score'):
                        st.progress(source['relevance_score'])
        else:
            st.info("ℹ️ No specific sources found. Answer generated from general knowledge.")
        
        # Display confidence with better styling
        confidence = response.get('confidence', 'unknown')
        confidence_emoji = get_confidence_badge(confidence)
        confidence_class = f"confidence-{confidence}" if confidence in ['high', 'medium', 'low'] else ""
        st.markdown(f'<p class="{confidence_class}">Confidence: {confidence_emoji} {confidence.upper()}</p>', unsafe_allow_html=True)
        
        # Show guardrail warning if triggered
        if response.get('guardrail_triggered'):
            st.warning("⚠️ **Guardrail Triggered:** This query was filtered for safety and appropriateness.")
        
        # Show if context was used
        if not response.get('context_used', True):
            st.info("ℹ️ **Limited Context:** Answer may be based on general knowledge rather than GitLab Handbook content.")
        
        # Show error if any
        if 'error' in response:
            st.error(f"⚠️ **Error:** {response['error']}")
        
        # Add to messages with performance data
        message_data = {
            "role": "assistant",
            "content": response['response'],
            "sources": response['sources'],
            "confidence": response['confidence'],
            "response_time": response.get('response_time', 0)
        }
        st.session_state.messages.append(message_data)
    
    # Auto-scroll (Streamlit handles this automatically)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Built with ❤️ by mridul<br>
    Powered by LangChain & Google Gemini AI
</div>
""", unsafe_allow_html=True)

