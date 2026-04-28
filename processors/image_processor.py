"""
processors/image_processor.py — Procesador de Imágenes
"""

from .base import BaseProcessor, ProcessingContext

class ImageProcessor(BaseProcessor):
    """
    Inserta imágenes en slides: URL, local, o placeholders IA.
    """
    
    name = "Image Processor"
    priority = 30
    
    async def process(self, ctx: ProcessingContext) -> None:
        slides = ctx.generated_structure.get("slides", [])
        
        for i, slide in enumerate(slides):
            img_prompt = slide.get("image_prompt")
            if not img_prompt:
                continue
            
            ctx.emit(f"🖼️ Procesando imagen para slide {i+1}")
            
            # Por ahora: placeholder visual con el prompt
            # En futura versión: integrar API de generación de imágenes
            ctx.engine.add_ai_image_placeholder(
                slide_index=i,
                prompt=img_prompt,
                left=6.8, top=1.8, width=5.5, height=5.0
            )
            
            ctx.emit(f"✅ Placeholder IA añadido: {img_prompt[:50]}...")
        
        # Procesar directivas explícitas del usuario
        for directive in ctx.image_directives:
            slide_idx = directive.get("slide", 0)
            img_type = directive.get("type")
            value = directive.get("value")
            
            try:
                if img_type == "url":
                    ctx.engine.add_image_from_url(slide_idx, value)
                elif img_type == "path":
                    ctx.engine.add_image_from_path(slide_idx, value)
                ctx.emit(f"✅ Imagen {img_type} añadida a slide {slide_idx}")
            except Exception as e:
                ctx.emit(f"⚠️ Error imagen slide {slide_idx}: {e}")