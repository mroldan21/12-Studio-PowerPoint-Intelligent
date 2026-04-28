"""Summary processor - creates summaries of content."""

from typing import Dict, Any
from .base import BaseProcessor


class SummaryProcessor(BaseProcessor):
    """Processes content to create summaries."""
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the content."""
        content = data.get("content", "")
        max_length = data.get("max_length", 200)
        
        # Simple summary - take first N characters
        summary = content[:max_length] + "..." if len(content) > max_length else content
        
        return {
            "summary": summary,
            "original_length": len(content),
            "summary_length": len(summary)
        }