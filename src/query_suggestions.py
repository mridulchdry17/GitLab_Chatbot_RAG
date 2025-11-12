"""
Query Suggestions Module
Provides helpful query suggestions based on available content
"""

from typing import List
import random


class QuerySuggestions:
    """Generate query suggestions for users"""
    
    SUGGESTIONS = [
        "What are GitLab's core values?",
        "How does GitLab handle remote work?",
        "What is GitLab's product direction?",
        "How does GitLab approach engineering?",
        "What are GitLab's security practices?",
        "How does GitLab handle customer success?",
        "What is GitLab's approach to transparency?",
        "How does GitLab manage teams?",
        "What are GitLab's hiring practices?",
        "How does GitLab approach diversity and inclusion?",
        "What is GitLab's compensation philosophy?",
        "How does GitLab handle performance reviews?",
        "What are GitLab's engineering principles?",
        "How does GitLab approach product development?",
        "What is GitLab's marketing strategy?",
    ]
    
    @classmethod
    def get_suggestions(cls, n: int = 4) -> List[str]:
        """Get random query suggestions"""
        return random.sample(cls.SUGGESTIONS, min(n, len(cls.SUGGESTIONS)))
    
    @classmethod
    def get_category_suggestions(cls, category: str) -> List[str]:
        """Get suggestions for a specific category"""
        category_map = {
            'values': [
                "What are GitLab's core values?",
                "How does GitLab practice transparency?",
                "What is GitLab's approach to collaboration?",
            ],
            'engineering': [
                "What are GitLab's engineering principles?",
                "How does GitLab handle code reviews?",
                "What is GitLab's approach to testing?",
            ],
            'product': [
                "What is GitLab's product direction?",
                "How does GitLab prioritize features?",
                "What is GitLab's product development process?",
            ],
            'people': [
                "How does GitLab handle remote work?",
                "What are GitLab's hiring practices?",
                "How does GitLab approach diversity and inclusion?",
            ]
        }
        return category_map.get(category.lower(), cls.get_suggestions(3))

