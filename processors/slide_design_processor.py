"""
processors/slide_design_processor.py — Procesador de Diseño Visual
"""

from core.slide_designer import SlideDesigner
from core.themes import ThemeRegistry
from .base import BaseProcessor, ProcessingContext


class SlideDesignProcessor(BaseProcessor):
    """
    Aplica el diseño visual a las slides generadas por IA.
    Soporta temas JSON, programáticos y plantillas PPTX.
    """

    name = "Slide Designer"
    priority = 10

    def __init__(self, theme_name: str = "pitchsync_dark"):
        self.theme_name = theme_name
        # Cargar temas disponibles
        ThemeRegistry.load_json_themes()

    async def process(self, ctx: ProcessingContext) -> None:
        if not ctx.generated_structure:
            ctx.emit("⚠️ No hay estructura generada para diseñar")
            return

        ctx.emit(f"🎨 Aplicando tema: {self.theme_name}")

        designer = SlideDesigner(self.theme_name)
        result = designer.build_presentation(
            ctx.engine,
            ctx.generated_structure
        )

        ctx.emit(f"✅ Diseño aplicado: {result['slides_created']} slides")
        if "template_used" in result:
            ctx.emit(f"📄 Plantilla usada: {result['template_used']}")