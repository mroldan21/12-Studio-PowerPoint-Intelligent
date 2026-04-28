"""
core/slide_designer.py — Diseñador Visual de Diapositivas
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from .pptx_engine import PPTXEngine

class SlideDesigner:
    """
    Aplica el tema visual y posiciona elementos en diapositivas.
    Traduce la estructura JSON generada por IA en un PPTX visualmente coherente.
    """
    
    def __init__(self, theme_name: str = "pitchsync_dark"):
        self.theme = self._load_theme(theme_name)
        self.colors = self.theme["colors"]
        self.typography = self.theme["typography"]
        self.layouts = self.theme["slide_layouts"]
        self.spacing = self.theme["spacing"]
    
    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        theme_path = Path(__file__).parent.parent / "config" / "themes" / f"{theme_name}.json"
        with open(theme_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Convierte hex #RRGGBB a RGBColor."""
        hex_color = hex_color.lstrip("#")
        return RGBColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    def apply_background(self, engine: PPTXEngine, slide_index: int, color_hex: str):
        """Aplica color de fondo a una diapositiva."""
        rgb = self._hex_to_rgb(color_hex)
        engine.set_slide_background_color(
            slide_index, rgb[0], rgb[1], rgb[2]
        )
    
    def add_title(self, engine: PPTXEngine, slide_index: int, text: str, 
                  layout_config: Dict[str, Any], font_size: int = None):
        """Añade un título estilizado a una diapositiva."""
        if not font_size:
            font_size = self.typography["title_sizes"]["slide_title"]
        
        pos = layout_config["title_position"]
        engine.add_text_box(
            slide_index=slide_index,
            text=text,
            left=pos["left"],
            top=pos["top"],
            width=pos["width"],
            height=pos["height"],
            font_size=font_size,
            bold=True,
            color=self._hex_to_rgb(self.colors["text_primary"])
        )
    
    def add_subtitle(self, engine: PPTXEngine, slide_index: int, text: str,
                     layout_config: Dict[str, Any]):
        """Añade un subtítulo."""
        if "subtitle_position" not in layout_config:
            return
        
        pos = layout_config["subtitle_position"]
        engine.add_text_box(
            slide_index=slide_index,
            text=text,
            left=pos["left"],
            top=pos["top"],
            width=pos["width"],
            height=pos["height"],
            font_size=self.typography["title_sizes"]["subtitle"],
            bold=False,
            color=self._hex_to_rgb(self.colors["text_secondary"])
        )
    
    def add_bullets(self, engine: PPTXEngine, slide_index: int, bullets: List[str],
                    layout_config: Dict[str, Any]):
        """Añade bullets estilizados."""
        pos = layout_config.get("content_position", layout_config.get("left_content"))
        if not pos:
            return
        
        # Crear textbox para bullets
        bullet_text = "\n".join([f"• {b}" for b in bullets])
        engine.add_text_box(
            slide_index=slide_index,
            text=bullet_text,
            left=pos["left"],
            top=pos["top"],
            width=pos["width"],
            height=pos["height"],
            font_size=self.typography["bullet_size"],
            bold=False,
            color=self._hex_to_rgb(self.colors["text_primary"])
        )
    
    def add_notes(self, engine: PPTXEngine, slide_index: int, notes: str):
        """Añade notas de orador."""
        if notes:
            engine.set_notes(slide_index, notes)
    
    def design_slide(self, engine: PPTXEngine, slide_index: int, 
                     slide_data: Dict[str, Any]):
        """
        Diseña una diapositiva completa según su tipo.
        """
        slide_type = slide_data.get("type", "content_slide")
        
        # Seleccionar layout y fondo
        if slide_type == "title_slide":
            layout = self.layouts["title_slide"]
            self.apply_background(engine, slide_index, layout["background"])
            self.add_title(engine, slide_index, slide_data.get("title", ""), layout,
                         self.typography["title_sizes"]["slide_title"])
            self.add_subtitle(engine, slide_index, slide_data.get("subtitle", ""), layout)
        
        elif slide_type == "content_slide":
            layout = self.layouts["content_slide"]
            self.apply_background(engine, slide_index, layout["background"])
            self.add_title(engine, slide_index, slide_data.get("title", ""), layout,
                         self.typography["title_sizes"]["section_title"])
            self.add_bullets(engine, slide_index, slide_data.get("bullets", []), layout)
        
        elif slide_type == "split_slide":
            layout = self.layouts["split_slide"]
            self.apply_background(engine, slide_index, layout["background"])
            self.add_title(engine, slide_index, slide_data.get("title", ""), layout,
                         self.typography["title_sizes"]["section_title"])
            # Contenido dividido (texto + placeholder imagen)
            self.add_bullets(engine, slide_index, slide_data.get("bullets", []), layout)
        
        elif slide_type == "image_slide":
            layout = self.layouts["image_slide"]
            self.apply_background(engine, slide_index, layout["background"])
            self.add_title(engine, slide_index, slide_data.get("title", ""), layout,
                         self.typography["title_sizes"]["section_title"])
            # La imagen se añade después vía image_processor
        
        elif slide_type == "section_divider":
            # Slide de transición con solo título grande centrado
            layout = self.layouts["title_slide"]
            self.apply_background(engine, slide_index, self.colors["secondary"])
            self.add_title(engine, slide_index, slide_data.get("title", ""), layout,
                         self.typography["title_sizes"]["slide_title"])
        
        # Añadir notas siempre
        self.add_notes(engine, slide_index, slide_data.get("notes", ""))
    
    def build_presentation(self, engine: PPTXEngine, structure: Dict[str, Any]):
        """
        Construye la presentación completa desde la estructura JSON.
        """
        slides_data = structure.get("slides", [])
        
        # Crear slides necesarias
        current_count = engine.slide_count
        needed = len(slides_data)
        
        # Asegurar que tenemos suficientes slides
        for _ in range(max(0, needed - current_count)):
            engine.add_blank_slide()
        
        # Diseñar cada slide
        for i, slide_data in enumerate(slides_data):
            self.design_slide(engine, i, slide_data)
        
        return {
            "slides_created": len(slides_data),
            "title": structure.get("title", "Untitled"),
            "model_used": structure.get("_meta", {}).get("model_name", "Unknown")
        }