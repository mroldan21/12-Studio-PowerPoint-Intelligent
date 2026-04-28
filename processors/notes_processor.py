"""
processors/notes_processor.py — Procesador de Notas
"""

from .base import BaseProcessor, ProcessingContext

class NotesProcessor(BaseProcessor):
    """
    Asegura que todas las slides tengan notas de orador.
    """
    
    name = "Notes Processor"
    priority = 40
    
    async def process(self, ctx: ProcessingContext) -> None:
        slides = ctx.generated_structure.get("slides", [])
        
        for i, slide in enumerate(slides):
            notes = slide.get("notes", "")
            if notes:
                ctx.engine.set_notes(i, notes)
        
        ctx.emit(f"✅ Notas aplicadas a {len(slides)} slides")