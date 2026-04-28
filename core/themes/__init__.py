"""
core/themes/__init__.py — Sistema de Temas Flexible
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE


class BaseTheme(ABC):
    """
    Clase base para todos los temas.
    """

    name: str = "base"
    display_name: str = "Base Theme"

    @abstractmethod
    def apply(self, engine, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica el tema a una presentación completa.
        Recibe el engine (con o sin plantilla cargada) y la estructura JSON.
        Retorna metadatos del resultado.
        """
        pass

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )


class JSONTheme(BaseTheme):
    """
    Tema basado en archivo JSON de configuración (compatible con el sistema anterior).
    """

    def __init__(self, theme_name: str):
        self.theme_name = theme_name
        self.config = self._load_config(theme_name)

    def _load_config(self, theme_name: str) -> Dict[str, Any]:
        theme_path = Path(__file__).parent.parent.parent / "config" / "themes" / f"{theme_name}.json"
        if not theme_path.exists():
            raise FileNotFoundError(f"Tema no encontrado: {theme_path}")
        with open(theme_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def apply(self, engine, structure: Dict[str, Any]) -> Dict[str, Any]:
        slides_data = structure.get("slides", [])
        current_count = engine.slide_count
        needed = len(slides_data)

        for _ in range(max(0, needed - current_count)):
            engine.add_blank_slide()

        colors = self.config.get("colors", {})
        bg = colors.get("background", "#080814")
        text = colors.get("text_primary", "#FFFFFF")
        text_rgb = self._hex_to_rgb(text)
        bg_rgb = self._hex_to_rgb(bg)

        for i, slide_data in enumerate(slides_data):
            slide_type = slide_data.get("type", "content_slide")
            title = slide_data.get("title", "")
            bullets = slide_data.get("bullets", [])
            notes = slide_data.get("notes", "")

            engine.set_slide_background_color(i, bg_rgb[0], bg_rgb[1], bg_rgb[2])

            if title:
                engine.add_text_box(i, title, 0.8, 0.5, 11.7, 1.0,
                                    font_size=36, bold=True, color=text_rgb)

            if bullets:
                bullet_text = "\n".join([f"• {b}" for b in bullets])
                engine.add_text_box(i, bullet_text, 0.8, 1.8, 11.7, 5.0,
                                    font_size=16, color=text_rgb)

            if notes:
                engine.set_notes(i, notes)

        return {"slides_created": len(slides_data), "title": structure.get("title", "Untitled")}


class ProgrammaticTheme(BaseTheme):
    """
    Tema programático definido en Python.
    Permite diseños complejos tipo PitchSync.
    """

    def __init__(self):
        super().__init__()
        self.W = 13.333
        self.H = 7.5

    @abstractmethod
    def render_title_slide(self, engine, slide_index: int, data: Dict[str, Any]):
        pass

    @abstractmethod
    def render_content_slide(self, engine, slide_index: int, data: Dict[str, Any]):
        pass

    @abstractmethod
    def render_section_divider(self, engine, slide_index: int, data: Dict[str, Any]):
        pass

    @abstractmethod
    def render_image_slide(self, engine, slide_index: int, data: Dict[str, Any]):
        pass

    @abstractmethod
    def render_split_slide(self, engine, slide_index: int, data: Dict[str, Any]):
        pass

    def apply(self, engine, structure: Dict[str, Any]) -> Dict[str, Any]:
        slides_data = structure.get("slides", [])
        current_count = engine.slide_count
        needed = len(slides_data)

        for _ in range(max(0, needed - current_count)):
            engine.add_blank_slide()

        for i, slide_data in enumerate(slides_data):
            slide_type = slide_data.get("type", "content_slide")
            if slide_type == "title_slide":
                self.render_title_slide(engine, i, slide_data)
            elif slide_type == "content_slide":
                self.render_content_slide(engine, i, slide_data)
            elif slide_type == "section_divider":
                self.render_section_divider(engine, i, slide_data)
            elif slide_type == "image_slide":
                self.render_image_slide(engine, i, slide_data)
            elif slide_type == "split_slide":
                self.render_split_slide(engine, i, slide_data)
            else:
                self.render_content_slide(engine, i, slide_data)

            notes = slide_data.get("notes", "")
            if notes:
                engine.set_notes(i, notes)

        return {
            "slides_created": len(slides_data),
            "title": structure.get("title", "Untitled")
        }


class TemplateTheme(BaseTheme):
    """
    Tema basado en plantilla PPTX importada.
    """

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")

    def apply(self, engine, structure: Dict[str, Any]) -> Dict[str, Any]:
        engine.load_from_path(str(self.template_path))

        slides_data = structure.get("slides", [])
        current = engine.slide_count
        for _ in range(max(0, len(slides_data) - current)):
            engine.add_blank_slide()

        for i, slide_data in enumerate(slides_data):
            if i < engine.slide_count:
                self._fill_slide(engine, i, slide_data)

        return {
            "slides_created": min(len(slides_data), engine.slide_count),
            "title": structure.get("title", "Untitled"),
            "template_used": str(self.template_path)
        }

    def _fill_slide(self, engine, slide_index: int, data: Dict[str, Any]):
        slide_type = data.get("type", "content_slide")
        title = data.get("title", "")
        bullets = data.get("bullets", [])

        if title:
            engine.add_text_box(
                slide_index, title,
                left=0.8, top=0.5, width=11.7, height=1.0,
                font_size=36, bold=True,
                color=(255, 255, 255)
            )

        if bullets:
            bullet_text = "\n".join([f"• {b}" for b in bullets])
            engine.add_text_box(
                slide_index, bullet_text,
                left=0.8, top=1.8, width=11.7, height=5.0,
                font_size=16,
                color=(255, 255, 255)
            )

        notes = data.get("notes", "")
        if notes:
            engine.set_notes(slide_index, notes)


class ThemeRegistry:
    """
    Registro central de temas disponibles.
    """

    _themes: Dict[str, BaseTheme] = {}

    @classmethod
    def register(cls, name: str, theme: BaseTheme):
        cls._themes[name] = theme

    @classmethod
    def get(cls, name: str) -> Optional[BaseTheme]:
        return cls._themes.get(name)

    @classmethod
    def list_themes(cls) -> List[Dict[str, str]]:
        return [
            {"id": name, "type": type(theme).__name__, "display": getattr(theme, 'display_name', name)}
            for name, theme in cls._themes.items()
        ]

    @classmethod
    def load_json_themes(cls):
        """Auto-registra todos los temas JSON de la carpeta config/themes."""
        themes_dir = Path(__file__).parent.parent.parent / "config" / "themes"
        if not themes_dir.exists():
            return
        for theme_file in themes_dir.glob("*.json"):
            name = theme_file.stem
            # Ignorar archivos de metadata (como pitchsync_cyber.json)
            if name.endswith("_meta"):
                continue
            try:
                theme = JSONTheme(name)
                cls.register(name, theme)
            except Exception as e:
                print(f"⚠️ Error cargando tema {name}: {e}")


# Registro de temas built-in
ThemeRegistry.register("pitchsync_dark", JSONTheme("pitchsync_dark"))