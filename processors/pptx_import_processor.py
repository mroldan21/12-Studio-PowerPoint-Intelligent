"""
processors/pptx_import_processor.py — Procesador de Importación PPTX
"""

import io
import re
from typing import Optional, List, Dict, Any
from pptx import Presentation
from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class PPTXImportProcessor(BaseProcessor):
    """
    Procesador especializado en importar y mejorar presentaciones PPTX existentes.
    Extrae contenido, analiza estructura y genera una versión mejorada con IA.
    """
    
    name = "PPTX Import Processor"
    priority = 5
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenRouterClient(api_key)
        self.orchestrator = ContentOrchestrator(self.client)
    
    async def process(self, ctx: ProcessingContext) -> None:
        """
        Importa un PPTX existente, extrae su contenido y genera una versión mejorada.
        """
        ctx.emit("📥 Importando y analizando PPTX...")
        
        prompt = ctx.metadata.get("prompt", "")
        model_id = ctx.metadata.get("model_id")
        
        # Verificar que el engine tenga una presentación cargada
        if not ctx.engine or ctx.engine.slide_count == 0:
            ctx.emit("⚠️ Error: No hay archivo PPTX cargado en el engine")
            raise ValueError("Se requiere un archivo PPTX para importar")
        
        # Extraer contenido del PPTX existente
        ctx.emit(f"📊 Analizando {ctx.engine.slide_count} diapositivas...")
        extracted_content = self._extract_pptx_content(ctx)
        
        ctx.emit(f"✅ Contenido extraído: {len(extracted_content['slides'])} slides con texto")
        ctx.emit(f"📝 {extracted_content['total_text_length']} caracteres totales")
        
        # Preparar contexto enriquecido para la IA
        import_context = self._build_import_context(extracted_content, prompt)
        
        ctx.emit(f"🤖 Generando versión mejorada con modelo: {model_id or 'default'}")
        if prompt:
            ctx.emit(f"🎯 Instrucciones adicionales: {prompt[:80]}...")
        
        # Generar nueva estructura mejorada
        result = await self.orchestrator.generate_from_prompt(
            prompt=f"Mejorar presentación: {extracted_content['title']}",
            input_type="pptx_import",
            model_id=model_id,
            context_text=import_context
        )
        
        # Guardar resultado en el contexto
        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name", "unknown")
        ctx.metadata["slide_count"] = len(result.get("slides", []))
        ctx.metadata["input_processed"] = "pptx_import"
        ctx.metadata["source_slide_count"] = ctx.engine.slide_count
        
        ctx.emit(f"✅ PPTX mejorado: {result.get('title', 'Sin título')}")
        ctx.emit(f"📊 {len(result.get('slides', []))} diapositivas generadas (original: {ctx.engine.slide_count})")
        
        # Análisis comparativo
        new_slides = result.get("slides", [])
        improvements = self._analyze_improvements(extracted_content, new_slides)
        
        ctx.emit(f"🔄 Mejoras aplicadas:")
        ctx.emit(f"   • Títulos mejorados: {improvements['titles_improved']}")
        ctx.emit(f"   • Contenido expandido: {improvements['content_expanded']}")
        ctx.emit(f"   • Notas añadidas: {improvements['notes_added']}")
        ctx.emit(f"   • Elementos visuales: {improvements['visual_elements']}")
    
    def _extract_pptx_content(self, ctx: ProcessingContext) -> Dict[str, Any]:
        """
        Extrae todo el contenido textual de un PPTX.
        """
        slides_content = []
        all_notes = []
        total_text = []
        
        for i in range(ctx.engine.slide_count):
            slide = ctx.engine.get_slide(i)
            
            # Extraer texto de shapes
            slide_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_texts.append(shape.text.strip())
            
            slide_text = "\\n".join(slide_texts)
            total_text.append(slide_text)
            
            # Extraer notas
            notes = ""
            try:
                notes = slide.notes_slide.notes_text_frame.text
                if notes.strip():
                    all_notes.append(notes.strip())
            except:
                pass
            
            slides_content.append({
                "index": i,
                "text": slide_text,
                "notes": notes,
                "has_notes": bool(notes.strip())
            })
        
        # Detectar título de la presentación
        title = "Presentación Importada"
        if slides_content and slides_content[0]["text"]:
            # Primera línea de la primera slide suele ser el título
            first_lines = slides_content[0]["text"].split("\\n")
            if first_lines:
                title = first_lines[0][:100]
        
        return {
            "title": title,
            "slides": slides_content,
            "total_text_length": sum(len(s["text"]) for s in slides_content),
            "has_notes": any(s["has_notes"] for s in slides_content),
            "notes_count": len(all_notes),
            "raw_slides": total_text
        }
    
    def _build_import_context(self, extracted: Dict, instructions: str) -> str:
        """
        Construye el contexto completo para la IA.
        """
        context_parts = []
        
        # Título original
        context_parts.append(f"TÍTULO ORIGINAL: {extracted['title']}")
        
        # Instrucciones del usuario
        if instructions:
            context_parts.append(f"\\nINSTRUCCIONES ESPECÍFICAS:\\n{instructions}")
        
        # Contenido de cada slide
        context_parts.append("\\nCONTENIDO ORIGINAL DE DIAPOSITIVAS:")
        
        for i, slide in enumerate(extracted["slides"][:15]):  # Limitar a 15 slides para no exceder contexto
            context_parts.append(f"\\n--- SLIDE {i+1} ---")
            context_parts.append(slide["text"][:500])  # Limitar texto por slide
            
            if slide["has_notes"] and slide["notes"]:
                context_parts.append(f"[NOTAS: {slide['notes'][:300]}...]")
        
        # Información sobre notas existentes
        if extracted["has_notes"]:
            context_parts.append(f"\\nℹ️ La presentación original tenía notas en {extracted['notes_count']} slides")
        else:
            context_parts.append("\\n⚠️ La presentación original NO tenía notas (se generarán nuevas)")
        
        # Guías de mejora
        context_parts.append("\\n\\nGUÍAS DE MEJORA:")
        context_parts.append("- Mantener el mensaje central pero mejorar la expresión")
        context_parts.append("- Convertir listas largas en bullets concisos")
        context_parts.append("- Añadir notas de orador donde no existan")
        context_parts.append("- Sugerir imágenes relevantes para conceptos clave")
        context_parts.append("- Mejorar títulos para que sean más impactantes")
        context_parts.append("- Organizar en secciones lógicas si es posible")
        
        return "\\n".join(context_parts)
    
    def _analyze_improvements(self, original: Dict, new_slides: List[Dict]) -> Dict[str, int]:
        """
        Analiza las mejoras realizadas comparando original vs nuevo.
        """
        original_slides = original["slides"]
        
        titles_improved = 0
        content_expanded = 0
        notes_added = 0
        visual_elements = 0
        
        for i, new_slide in enumerate(new_slides):
            # Comparar con slide original si existe
            if i < len(original_slides):
                orig = original_slides[i]
                
                # Verificar si el título cambió
                if new_slide.get("title") and orig["text"]:
                    orig_title = orig["text"].split("\\n")[0] if orig["text"] else ""
                    if new_slide["title"] != orig_title[:100]:
                        titles_improved += 1
                
                # Verificar si se añadieron bullets
                if len(new_slide.get("bullets", [])) > 0:
                    content_expanded += 1
                
                # Verificar notas
                if new_slide.get("notes") and not orig["has_notes"]:
                    notes_added += 1
                
                # Elementos visuales
                if new_slide.get("type") == "image_slide" or new_slide.get("image_prompt"):
                    visual_elements += 1
            else:
                # Slides nuevos añadidos
                content_expanded += 1
                if new_slide.get("notes"):
                    notes_added += 1
        
        return {
            "titles_improved": min(titles_improved, len(new_slides)),
            "content_expanded": min(content_expanded, len(new_slides)),
            "notes_added": min(notes_added, len(new_slides)),
            "visual_elements": visual_elements
        }