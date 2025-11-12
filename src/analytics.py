"""
Analytics and Insights Module
Tracks usage patterns and provides insights
"""

from typing import List, Dict
from collections import Counter
import json
import os
from datetime import datetime


class Analytics:
    """Track and analyze chatbot usage"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.analytics_file = os.path.join(data_dir, 'analytics.json')
        os.makedirs(data_dir, exist_ok=True)
        self.load_analytics()
    
    def load_analytics(self):
        """Load analytics data"""
        if os.path.exists(self.analytics_file):
            with open(self.analytics_file, 'r') as f:
                self.data = json.load(f)
            # Convert dicts back to Counter objects for proper incrementing
            if isinstance(self.data.get('sources_accessed'), dict):
                self.data['sources_accessed'] = Counter(self.data['sources_accessed'])
            if isinstance(self.data.get('confidence_distribution'), dict):
                self.data['confidence_distribution'] = Counter(self.data['confidence_distribution'])
        else:
            self.data = {
                'total_queries': 0,
                'queries': [],
                'sources_accessed': Counter(),
                'confidence_distribution': Counter(),
                'guardrail_triggers': 0,
                'errors': 0
            }
    
    def save_analytics(self):
        """Save analytics data"""
        # Convert Counter objects to dict for JSON serialization
        data_to_save = self.data.copy()
        if isinstance(data_to_save.get('sources_accessed'), Counter):
            data_to_save['sources_accessed'] = dict(data_to_save['sources_accessed'])
        if isinstance(data_to_save.get('confidence_distribution'), Counter):
            data_to_save['confidence_distribution'] = dict(data_to_save['confidence_distribution'])
        
        with open(self.analytics_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    
    def track_query(self, query: str, response: Dict):
        """Track a query and its response"""
        self.data['total_queries'] += 1
        
        query_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'confidence': response.get('confidence', 'unknown'),
            'sources_count': len(response.get('sources', [])),
            'guardrail_triggered': response.get('guardrail_triggered', False),
            'error': 'error' in response
        }
        
        self.data['queries'].append(query_entry)
        
        # Track sources
        for source in response.get('sources', []):
            url = source.get('url', 'unknown')
            # Ensure sources_accessed is a Counter (handles both Counter and dict)
            if not isinstance(self.data['sources_accessed'], Counter):
                self.data['sources_accessed'] = Counter(self.data['sources_accessed'])
            self.data['sources_accessed'][url] += 1
        
        # Track confidence
        self.data['confidence_distribution'][response.get('confidence', 'unknown')] += 1
        
        # Track guardrails
        if response.get('guardrail_triggered'):
            self.data['guardrail_triggers'] += 1
        
        # Track errors
        if 'error' in response:
            self.data['errors'] += 1
        
        # Keep only last 1000 queries
        if len(self.data['queries']) > 1000:
            self.data['queries'] = self.data['queries'][-1000:]
        
        self.save_analytics()
    
    def get_insights(self) -> Dict:
        """Get analytics insights"""
        # Ensure Counter objects are used (convert from dict if needed)
        if isinstance(self.data.get('sources_accessed'), dict):
            self.data['sources_accessed'] = Counter(self.data['sources_accessed'])
        if isinstance(self.data.get('confidence_distribution'), dict):
            self.data['confidence_distribution'] = Counter(self.data['confidence_distribution'])
        
        total = self.data['total_queries']
        if total == 0:
            return {
                'total_queries': 0,
                'message': 'No queries yet'
            }
        
        # Most accessed sources
        sources = self.data['sources_accessed']
        if isinstance(sources, Counter):
            top_sources = dict(sources.most_common(5))
        else:
            # Fallback for dict: sort by value and take top 5
            top_sources = dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Average confidence
        conf_dist = self.data['confidence_distribution']
        if conf_dist:
            high_conf = conf_dist.get('high', 0)
            medium_conf = conf_dist.get('medium', 0)
            low_conf = conf_dist.get('low', 0)
            avg_confidence_score = (high_conf * 1.0 + medium_conf * 0.5 + low_conf * 0.0) / total
        else:
            avg_confidence_score = 0
        
        return {
            'total_queries': total,
            'top_sources': top_sources,
            'confidence_distribution': dict(conf_dist),
            'average_confidence': round(avg_confidence_score, 2),
            'guardrail_triggers': self.data['guardrail_triggers'],
            'error_rate': round(self.data['errors'] / total * 100, 2) if total > 0 else 0,
            'recent_queries': self.data['queries'][-10:] if len(self.data['queries']) > 10 else self.data['queries']
        }

