"""
Utility functions for the chatbot application
"""

import streamlit as st
from typing import Dict, List
import json


def format_source_citation(source: Dict) -> str:
    """Format a source for display"""
    section = source.get('section_title', 'Unknown Section')
    url = source.get('url', '#')
    
    # Only show clickable link if URL is valid
    if url and url.startswith('http'):
        return f"📄 [{section}]({url})"
    elif section:
        return f"📄 {section}"
    else:
        return "📄 Source"


def save_conversation_history(history: List[Dict], filename: str = 'conversation_history.json'):
    """Save conversation history to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")


def load_conversation_history(filename: str = 'conversation_history.json') -> List[Dict]:
    """Load conversation history from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def get_confidence_badge(confidence: str) -> str:
    """Get emoji badge for confidence level"""
    badges = {
        'high': '🟢 High',
        'medium': '🟡 Medium',
        'low': '🔴 Low'
    }
    return badges.get(confidence, '❓ Unknown')

