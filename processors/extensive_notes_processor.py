"""Extensive notes processor - creates detailed speaker notes."""

from typing import Dict, Any
from .base import BaseProcessor


class ExtensiveNotesProcessor(BaseProcessor):
    """Creates extensive speaker notes for presentations."""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate extensive notes."""
        slide_content = data.get("content", "")
        slide_title = data.get("title", "")
        
        notes = self._generate_extensive_notes(slide_title, slide_content)
        
        return {
            "notes": notes,
            "key_points": self._extract_key_points(slide_content),
            "timing": self._estimate_timing(slide_content)
        }
    
    def _generate_extensive_notes(self, title: str, content: str) -> str:
        """Generate detailed speaker notes."""
        return f"Speaker notes for: {title}\n\n{content}\n\nAdditional context and talking points."
    
    def _extract_key_points(self, content: str) -> list:
        """Extract key points from content."""
        return ["Point 1", "Point 2", "Point 3"]
    
    def _estimate_timing(self, content: str) -> int:
        """Estimate speaking time in seconds."""
        words = len(content.split())
        return max(30, words * 10)  # ~10 words per minute