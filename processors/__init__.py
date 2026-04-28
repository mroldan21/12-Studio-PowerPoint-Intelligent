"""
processors/__init__.py — Package de procesadores PPTX
"""

from .base import BaseProcessor, ProcessingContext
from .ai_content_processor import AIContentProcessor
from .summary_processor import SummaryProcessor
from .extensive_notes_processor import ExtensiveNotesProcessor
from .research_processor import ResearchProcessor
from .pptx_import_processor import PPTXImportProcessor
from .slide_design_processor import SlideDesignProcessor
from .image_processor import ImageProcessor
from .notes_processor import NotesProcessor

__all__ = [
    "BaseProcessor",
    "ProcessingContext",
    "AIContentProcessor",
    "SummaryProcessor",
    "ExtensiveNotesProcessor",
    "ResearchProcessor",
    "PPTXImportProcessor",
    "SlideDesignProcessor",
    "ImageProcessor",
    "NotesProcessor",
]