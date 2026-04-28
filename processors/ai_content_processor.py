"""
processors/ai_content_processor.py — Procesador de Generación de Contenido IA
"""

from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class AIContentProcessor(BaseProcessor):
    """
    Procesador que genera la estructura completa de la presentación vía IA.
    Debe ejecutarse PRIMERO en el pipeline (prioridad baja).
    """
    
    name = "AI Content Generator"
    priority = 5  # Primero
    
    def __init__(self, api_key: str = None):
        self.client = OpenRouterClient(api_key)
        self.orchestrator = ContentOrchestrator(self.client)
    
    async def process(self, ctx: ProcessingContext) -> None:
        ctx.emit(f"🤖 Generando contenido con modelo: {ctx.metadata.get('model_id', 'default')}")
        
        result = await self.orchestrator.generate_from_prompt(
            prompt=ctx.metadata.get("prompt", ""),
            input_type=ctx.metadata.get("input_type", "summary"),
            model_id=ctx.metadata.get("model_id"),
            context_text=ctx.notes_text or None
        )
        
        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name")
        ctx.metadata["slide_count"] = result.get("_meta", {}).get("slide_count")
        
        ctx.emit(f"✅ Estructura generada: {result.get('title')} ({len(result.get('slides', []))} slides)")