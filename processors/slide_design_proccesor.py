"""
processors/slide_design_processor.py — Procesador de Diseño Visual
"""

from core.slide_designer import SlideDesigner
from .base import BaseProcessor, ProcessingContext

class SlideDesignProcessor(BaseProcessor):
    """
    Aplica el diseño visual a las slides generadas por IA.
    """
    
    name = "Slide Designer"
    priority = 10  # Después de generación de contenido
    
    def __init__(self, theme_name: str = "pitchsync_dark"):
        self.designer = SlideDesigner(theme_name)
    
    async def process(self, ctx: ProcessingContext) -> None:
        if not ctx.generated_structure:
            ctx.emit("⚠️ No hay estructura generada para diseñar")
            return
        
        ctx.emit("🎨 Aplicando diseño visual PitchSync...")
        
        result = self.designer.build_presentation(
            ctx.engine,
            ctx.generated_structure
        )
        
        ctx.emit(f"✅ Diseño aplicado: {result['slides_created']} slides")