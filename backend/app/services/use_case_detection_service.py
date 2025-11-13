"""
Use Case Auto-Detection Service

Automatically detects the appropriate use case (CU1-CU6) from query patterns,
enabling automatic prompt optimization without requiring explicit use_case parameter.

Detection is based on keywords, patterns, and query structure analysis.
Falls back to None if no clear match is found (uses standard RAG prompt).
"""

import re
from typing import Optional

from app.schemas.use_cases import UseCaseType


class UseCaseDetectionService:
    """
    Service for automatically detecting the appropriate use case from a query.
    
    Uses pattern matching and keyword analysis to identify query intent
    and suggest the optimal use case for prompt generation.
    """
    
    def __init__(self):
        """Initialize detection patterns for each use case."""
        
        # CU1: Professional Content Generation
        self.cu1_patterns = [
            r'\b(write|draft|compose|create)\s+(report|email|letter|document|essay|article|memo|proposal)',
            r'\b(formal|professional|business|official)\s+(document|writing|communication|letter|email|proposal)',
            r'\b(business|formal)\s+(report|proposal)',
            r'\bgenerate\s+a\s+(report|document|essay|proposal)',
        ]
        self.cu1_keywords = ['formal', 'professional', 'business communication', 'official', 'draft', 'proposal']
        
        # CU2: Code Development
        self.cu2_patterns = [
            r'\b(write|create|generate|build|scrivi)\s+(code|function|class|component|script|funzione|codice)',
            r'\b(debug|fix|refactor|optimize)\s+(code|function|bug|error)',
            r'\b(implement|develop)\s+\w+\s+(in|using)\s+(python|javascript|react|java|c\+\+)',
            r'\bfunction\s+(to|that|for)',
            r'\bcomponent\s+(for|to)',
            r'\bfunzione\s+(python|javascript)',
        ]
        self.cu2_keywords = ['code', 'codice', 'function', 'funzione', 'debug', 'refactor', 'implement', 'algorithm', 'class']
        
        # CU3: Data Analysis & Document Synthesis
        self.cu3_patterns = [
            r'\b(summarize|summary|sum up|recap)',
            r'\b(analyze|analysis|examine|evaluate)',
            r'\b(extract|find|identify)\s+(key\s+)?(points|insights|trends|patterns|data)',
            r'\bkey\s+(points|takeaways|findings|insights)',
            r'\bmain\s+(points|ideas|themes|findings)',
            r'\bwhat\s+are\s+the\s+(main|key|important)',
        ]
        self.cu3_keywords = ['summarize', 'analyze', 'extract', 'key points', 'insights', 'trends']
        
        # CU4: Creative Brainstorming (Lists with quantities)
        self.cu4_patterns = [
            r'\b(list|lista)\s+(of|di)\s+\d+',
            r'\b(give|dammi|voglio|need|genera)\s+.*\d+\s+(ideas?|idee|names?|nomi|titles?|titoli|people|persone)',
            r'\d+\s+(ideas?|idee|options?|opzioni|alternatives?|alternative|suggestions?|suggerimenti)',
            r'\bbrainstorm',
            r'\b(generate|create)\s+\d+',
            r'\bexactly\s+\d+',
            r'\besattamente\s+\d+',
        ]
        self.cu4_keywords = ['list', 'lista', 'ideas', 'idee', 'brainstorm', 'alternatives', 'suggestions']
        
        # CU5: Structured Planning
        self.cu5_patterns = [
            r'\b(outline|structure|plan|roadmap|schema|framework)',
            r'\b(create|build|develop)\s+a\s+(plan|roadmap|structure|outline)',
            r'\bsteps\s+(to|for)',
            r'\bhow\s+to\s+(organize|structure|plan)',
            r'\b(project|study|course)\s+(plan|outline|structure)',
        ]
        self.cu5_keywords = ['outline', 'plan', 'roadmap', 'structure', 'steps', 'framework', 'organize']
        
        # CU6: Business Strategy
        self.cu6_patterns = [
            r'\b(swot|pestel|porter|business\s+model|value\s+proposition)',
            r'\b(strategic|strategy)\s+(analysis|plan|document)',
            r'\b(business\s+case|market\s+analysis|competitive\s+(analysis|landscape))',
            r'\b(strengths?|weaknesses?|opportunities|threats)\s+(and|,)',
        ]
        self.cu6_keywords = ['swot', 'pestel', 'business strategy', 'strategic', 'market analysis', 'competitive']
    
    def detect_use_case(self, query: str) -> Optional[UseCaseType]:
        """
        Detect the most appropriate use case for a given query.
        
        Args:
            query: The user's query text
            
        Returns:
            UseCaseType if a clear match is found, None otherwise
        """
        query_lower = query.lower()
        
        # Score each use case based on pattern and keyword matches
        scores = {
            UseCaseType.PROFESSIONAL_CONTENT: self._score_use_case(
                query_lower, self.cu1_patterns, self.cu1_keywords
            ),
            UseCaseType.CODE_DEVELOPMENT: self._score_use_case(
                query_lower, self.cu2_patterns, self.cu2_keywords
            ),
            UseCaseType.DATA_ANALYSIS: self._score_use_case(
                query_lower, self.cu3_patterns, self.cu3_keywords
            ),
            UseCaseType.CREATIVE_BRAINSTORMING: self._score_use_case(
                query_lower, self.cu4_patterns, self.cu4_keywords
            ),
            UseCaseType.STRUCTURED_PLANNING: self._score_use_case(
                query_lower, self.cu5_patterns, self.cu5_keywords
            ),
            UseCaseType.BUSINESS_STRATEGY: self._score_use_case(
                query_lower, self.cu6_patterns, self.cu6_keywords
            ),
        }
        
        # Find the use case with highest score
        max_score = max(scores.values())
        
        # Only return a use case if the score is significant (> 0)
        # This ensures we only auto-apply when there's a clear match
        if max_score > 0:
            detected_use_case = max(scores.items(), key=lambda x: x[1])[0]
            print(f"DEBUG [UseCaseDetection]: Detected {detected_use_case} (score: {max_score})")
            return detected_use_case
        
        print("DEBUG [UseCaseDetection]: No clear use case detected, using standard RAG")
        return None
    
    def _score_use_case(
        self, 
        query: str, 
        patterns: list[str], 
        keywords: list[str]
    ) -> int:
        """
        Calculate a score for a use case based on pattern and keyword matches.
        
        Args:
            query: The query text (lowercase)
            patterns: List of regex patterns to match
            keywords: List of keywords to check
            
        Returns:
            Score (higher = better match)
        """
        score = 0
        
        # Check regex patterns (weight: 3 points per match)
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 3
        
        # Check keywords (weight: 1 point per match)
        for keyword in keywords:
            if keyword.lower() in query:
                score += 1
        
        return score
    
    def get_confidence_level(self, query: str) -> tuple[Optional[UseCaseType], str]:
        """
        Detect use case with confidence level.
        
        Args:
            query: The user's query text
            
        Returns:
            Tuple of (UseCaseType or None, confidence_level)
            Confidence levels: 'high', 'medium', 'low', 'none'
        """
        query_lower = query.lower()
        
        # Calculate scores for all use cases
        scores = {
            UseCaseType.PROFESSIONAL_CONTENT: self._score_use_case(
                query_lower, self.cu1_patterns, self.cu1_keywords
            ),
            UseCaseType.CODE_DEVELOPMENT: self._score_use_case(
                query_lower, self.cu2_patterns, self.cu2_keywords
            ),
            UseCaseType.DATA_ANALYSIS: self._score_use_case(
                query_lower, self.cu3_patterns, self.cu3_keywords
            ),
            UseCaseType.CREATIVE_BRAINSTORMING: self._score_use_case(
                query_lower, self.cu4_patterns, self.cu4_keywords
            ),
            UseCaseType.STRUCTURED_PLANNING: self._score_use_case(
                query_lower, self.cu5_patterns, self.cu5_keywords
            ),
            UseCaseType.BUSINESS_STRATEGY: self._score_use_case(
                query_lower, self.cu6_patterns, self.cu6_keywords
            ),
        }
        
        max_score = max(scores.values())
        
        if max_score == 0:
            return None, 'none'
        
        detected_use_case = max(scores.items(), key=lambda x: x[1])[0]
        
        # Determine confidence level based on score
        if max_score >= 5:
            confidence = 'high'
        elif max_score >= 3:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return detected_use_case, confidence


# Singleton instance
use_case_detection_service = UseCaseDetectionService()
