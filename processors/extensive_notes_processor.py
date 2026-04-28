"""
processors/extensive_notes_processor.py — Procesador de Apuntes Extensos
"""

from typing import Optional
from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class ExtensiveNotesProcessor(BaseProcessor):
    """
    Procesador especializado en convertir apuntes extensos en presentaciones estructuradas.
    Optimizado para contenido académico, documentación técnica y materiales de estudio.
    """
    
    name = "Extensive Notes Processor"
    priority = 5
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenRouterClient(api_key)
        self.orchestrator = ContentOrchestrator(self.client)
    
    async def process(self, ctx: ProcessingContext) -> None:
        """
        Procesa apuntes extensos y genera una presentación académica estructurada.
        """
        ctx.emit("📚 Procesando apuntes extensos...")
        
        notes_text = ctx.metadata.get("prompt", "")
        model_id = ctx.metadata.get("model_id")
        
        if not notes_text:
            ctx.emit("⚠️ Error: No se proporcionaron apuntes")
            raise ValueError("Los apuntes son requeridos para el procesamiento")
        
        # Estadísticas del texto
        word_count = len(notes_text.split())
        char_count = len(notes_text)
        
        ctx.emit(f"📊 Texto recibido: {word_count} palabras, {char_count} caracteres")
        ctx.emit(f"🤖 Generando estructura académica con modelo: {model_id or 'default'}")
        
        # Detectar si hay contenido markdown o estructuras especiales
        has_headers = notes_text.count('#') > 0
        has_lists = notes_text.count('-') > 5 or notes_text.count('*') > 5
        
        if has_headers:
            ctx.emit("📋 Detectadas cabeceras markdown")
        if has_lists:
            ctx.emit("📋 Detectadas listas estructuradas")
        
        # Generar estructura usando el orchestrator con tipo 'extensive_notes'
        result = await self.orchestrator.generate_from_prompt(
            prompt=notes_text,
            input_type="extensive_notes",
            model_id=model_id,
            context_text=None
        )
        
        # Guardar resultado en el contexto
        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name", "unknown")
        ctx.metadata["slide_count"] = len(result.get("slides", []))
        ctx.metadata["input_processed"] = "extensive_notes"
        ctx.metadata["source_word_count"] = word_count
        
        ctx.emit(f"✅ Apuntes procesados: {result.get('title', 'Sin título')}")
        ctx.emit(f"📊 {len(result.get('slides', []))} diapositivas generadas desde {word_count} palabras")
        
        # Análisis de la estructura generada
        slides = result.get("slides", [])
        section_dividers = [s for s in slides if s.get("type") == "section_divider"]
        content_slides = [s for s in slides if s.get("type") == "content_slide"]
        image_slides = [s for s in slides if s.get("type") == "image_slide"]
        
        ctx.emit(f"🗂️ Secciones: {len(section_dividers)} | Contenido: {len(content_slides)} | Imágenes: {len(image_slides)}")
        
        # Verificar que haya notas suficientes
        slides_with_notes = sum(1 for s in slides if s.get("notes"))
        ctx.emit(f"📝 {slides_with_notes}/{len(slides)} slides tienen notas de orador")