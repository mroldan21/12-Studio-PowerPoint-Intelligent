"""
processors/research_processor.py — Procesador de Investigación Académica
"""

import io
from typing import Optional
from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class ResearchProcessor(BaseProcessor):
    """
    Procesador especializado en presentaciones de investigación académica.
    Genera estructuras rigurosas con: Introducción, Metodología, Resultados, Conclusión.
    """
    
    name = "Research Processor"
    priority = 5
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenRouterClient(api_key)
        self.orchestrator = ContentOrchestrator(self.client)
    
    async def process(self, ctx: ProcessingContext) -> None:
        """
        Procesa un tema de investigación y genera una presentación académica formal.
        """
        ctx.emit("🔬 Procesando tema de investigación...")
        
        research_topic = ctx.metadata.get("prompt", "")
        model_id = ctx.metadata.get("model_id")
        
        if not research_topic:
            ctx.emit("⚠️ Error: No se proporcionó tema de investigación")
            raise ValueError("El tema de investigación es requerido")
        
        # Construir contexto de investigación
        context_parts = []
        
        # Si hay notas adicionales (bibliografía, datos, etc.)
        if ctx.notes_text:
            context_parts.append(f"CONTEXTO ADICIONAL:\n{ctx.notes_text}")
            ctx.emit("📄 Contexto adicional detectado")
        
        # Instrucciones específicas para investigación
        research_context = """
ESTRUCTURA REQUERIDA PARA INVESTIGACIÓN ACADÉMICA:
1. Portada (título, autores, institución, fecha)
2. Introducción (contexto, problema, objetivos)
3. Marco Teórico (fundamentos, literatura relevante)
4. Metodología (diseño, muestra, instrumentos, procedimiento)
5. Resultados (hallazgos principales con datos/estadísticas)
6. Discusión (interpretación de resultados)
7. Conclusiones (aportes, limitaciones, trabajos futuros)
8. Referencias (formato académico)

NOTAS: Deben incluir citas relevantes y contexto para la defensa.
IMÁGENES: Diagramas metodológicos, gráficos de resultados, tablas.
"""
        context_parts.append(research_context)
        
        full_context = "\n\n".join(context_parts) if context_parts else None
        
        ctx.emit(f"🤖 Generando estructura de investigación con modelo: {model_id or 'default'}")
        ctx.emit(f"📋 Tema: {research_topic[:80]}...")
        
        # Generar estructura usando el orchestrator con tipo 'research'
        result = await self.orchestrator.generate_from_prompt(
            prompt=research_topic,
            input_type="research",
            model_id=model_id,
            context_text=full_context
        )
        
        # Guardar resultado en el contexto
        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name", "unknown")
        ctx.metadata["slide_count"] = len(result.get("slides", []))
        ctx.metadata["input_processed"] = "research"
        
        ctx.emit(f"✅ Investigación procesada: {result.get('title', 'Sin título')}")
        ctx.emit(f"📊 {len(result.get('slides', []))} diapositivas académicas generadas")
        
        # Análisis detallado de la estructura académica
        slides = result.get("slides", [])
        
        # Identificar tipos de slides
        title_slides = [s for s in slides if s.get("type") == "title_slide"]
        content_slides = [s for s in slides if s.get("type") == "content_slide"]
        section_dividers = [s for s in slides if s.get("type") == "section_divider"]
        split_slides = [s for s in slides if s.get("type") == "split_slide"]
        image_slides = [s for s in slides if s.get("type") == "image_slide"]
        
        ctx.emit(f"🎯 Estructura: {len(title_slides)} títulos, {len(content_slides)} contenido")
        ctx.emit(f"🖼️ {len(image_slides)} diapositivas con elementos visuales")
        ctx.emit(f"🗂️ {len(section_dividers)} divisores de sección")
        
        # Verificar calidad académica
        slides_with_notes = sum(1 for s in slides if s.get("notes") and len(s.get("notes", "")) > 50)
        slides_with_multiple_bullets = sum(1 for s in slides if len(s.get("bullets", [])) >= 3)
        
        ctx.emit(f"📝 {slides_with_notes}/{len(slides)} slides tienen notas detalladas")
        ctx.emit(f"✓ {slides_with_multiple_bullets} slides tienen contenido sustancial")
        
        # Sugerencias para mejora
        if len(image_slides) < 2:
            ctx.emit("💡 Sugerencia: Considerar añadir más diagramas o figuras")