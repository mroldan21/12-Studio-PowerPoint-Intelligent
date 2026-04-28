"""
processors/summary_processor.py — Procesador de Resúmenes
"""

from typing import Optional
from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class SummaryProcessor(BaseProcessor):
    """
    Procesador especializado en generar presentaciones desde resúmenes breves.
    Optimizado para prompts concisos y generación rápida.
    """
    
    name = "Summary Processor"
    priority = 5
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenRouterClient(api_key)
        self.orchestrator = ContentOrchestrator(self.client)
    
    async def process(self, ctx: ProcessingContext) -> None:
        """
        Procesa un resumen breve y genera la estructura de la presentación.
        """
        ctx.emit("📝 Procesando resumen breve...")
        
        prompt = ctx.metadata.get("prompt", "")
        model_id = ctx.metadata.get("model_id")
        
        if not prompt:
            ctx.emit("⚠️ Error: No se proporcionó prompt")
            raise ValueError("El prompt es requerido para procesar un resumen")
        
        ctx.emit(f"🤖 Generando estructura desde resumen con modelo: {model_id or 'default'}")
        
        # Generar estructura usando el orchestrator con tipo 'summary'
        result = await self.orchestrator.generate_from_prompt(
            prompt=prompt,
            input_type="summary",
            model_id=model_id,
            context_text=ctx.notes_text or None
        )
        
        # Guardar resultado en el contexto
        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name", "unknown")
        ctx.metadata["slide_count"] = len(result.get("slides", []))
        ctx.metadata["input_processed"] = "summary"
        
        ctx.emit(f"✅ Resumen procesado: {result.get('title', 'Sin título')}")
        ctx.emit(f"📊 {len(result.get('slides', []))} diapositivas generadas")
        
        # Log adicional de información
        slides = result.get("slides", [])
        content_slides = [s for s in slides if s.get("type") == "content_slide"]
        image_slides = [s for s in slides if s.get("type") == "image_slide"]
        
        ctx.emit(f"🎯 Contenido: {len(content_slides)} slides, {len(image_slides)} con imágenes")