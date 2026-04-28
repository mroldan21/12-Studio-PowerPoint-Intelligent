"""
core/slide_designer.py — Diseñador Visual de Diapositivas
Ahora delega en el sistema de temas.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from .pptx_engine import PPTXEngine
from .themes import ThemeRegistry


class SlideDesigner:
    """
    Diseñador que aplica temas visuales a diapositivas.
    Mantiene compatibilidad con el sistema anterior.
    """

    def __init__(self, theme_name: str = "pitchsync_dark"):
        self.theme_name = theme_name
        self.theme = ThemeRegistry.get(theme_name)

        # Fallback a tema JSON si no está registrado
        if not self.theme:
            from .themes import JSONTheme
            self.theme = JSONTheme(theme_name)

    def build_presentation(self, engine: PPTXEngine, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye la presentación completa usando el tema seleccionado.
        """
        if self.theme:
            return self.theme.apply(engine, structure)
        else:
            # Fallback básico
            return self._build_basic(engine, structure)

    def _build_basic(self, engine: PPTXEngine, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Construcción básica sin tema."""
        slides_data = structure.get("slides", [])
        for _ in range(max(0, len(slides_data) - engine.slide_count)):
            engine.add_blank_slide()

        for i, slide_data in enumerate(slides_data):
            title = slide_data.get("title", "")
            bullets = slide_data.get("bullets", [])
            notes = slide_data.get("notes", "")

            engine.set_slide_background_color(i, 8, 8, 20)

            if title:
                engine.add_text_box(i, title, 0.8, 0.5, 11.7, 1.0,
                                    font_size=36, bold=True, color=(255, 255, 255))

            if bullets:
                text = "\n".join([f"• {b}" for b in bullets])
                engine.add_text_box(i, text, 0.8, 1.8, 11.7, 5.0,
                                    font_size=16, color=(255, 255, 255))

            if notes:
                engine.set_notes(i, notes)

        return {"slides_created": len(slides_data), "title": structure.get("title", "Untitled")}

    # ── Métodos legacy para compatibilidad ─────────────────────────────────

    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        theme_path = Path(__file__).parent.parent / "config" / "themes" / f"{theme_name}.json"
        with open(theme_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        hex_color = hex_color.lstrip("#")
        return RGBColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )

    def apply_background(self, engine: PPTXEngine, slide_index: int, color_hex: str):
        rgb = self._hex_to_rgb(color_hex)
        engine.set_slide_background_color(slide_index, rgb[0], rgb[1], rgb[2])

    def add_title(self, engine: PPTXEngine, slide_index: int, text: str,
                  layout_config: Dict[str, Any], font_size: int = None):
        if not font_size:
            font_size = 36
        pos = layout_config["title_position"]
        engine.add_text_box(
            slide_index=slide_index, text=text,
            left=pos["left"], top=pos["top"],
            width=pos["width"], height=pos["height"],
            font_size=font_size, bold=True,
            color=self._hex_to_rgb("#FFFFFF")
        )

    def build_presentation(self, engine: PPTXEngine, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Alias para compatibilidad."""
        return self.build_presentation(engine, structure)