"""
core/themes/pitchsync_theme.py — Tema PitchSync Cyberpunk
Basado en gen_pptx.py — estética cyberpunk con bordes neón, tarjetas y grids.
"""

from typing import Dict, Any, Tuple
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from core.pptx_engine import PPTXEngine
from . import ProgrammaticTheme


# ── Paleta PitchSync ─────────────────────────────────────────────────────────
BG      = (0x08, 0x08, 0x14)
CARD    = (0x10, 0x10, 0x22)
CARD2   = (0x1A, 0x1A, 0x30)
CYAN    = (0x00, 0xE5, 0xCC)
MAGENTA = (0xEE, 0x00, 0xBB)
ORANGE  = (0xFF, 0x80, 0x00)
GREEN   = (0x00, 0xFF, 0x88)
YELLOW  = (0xFF, 0xDD, 0x00)
WHITE   = (0xFF, 0xFF, 0xFF)
LGRAY   = (0x88, 0x99, 0xAA)
PURPLE  = (0x99, 0x00, 0xFF)
DARK_BG = (0x05, 0x07, 0x14)


class PitchSyncTheme(ProgrammaticTheme):
    """
    Tema cyberpunk PitchSync con bordes neón, tarjetas y layouts avanzados.
    """

    name = "pitchsync_cyber"
    display_name = "PitchSync Cyberpunk"

    def __init__(self):
        super().__init__()
        self.W = 13.333  # slide width inches
        self.H = 7.5     # slide height inches

    def _setup_slide(self, engine: PPTXEngine, slide_index: int,
                     bg_color: Tuple[int, int, int] = BG,
                     top_bar: Tuple[int, int, int] = None,
                     bottom_bar: Tuple[int, int, int] = None):
        """Configura fondo y barras decorativas de una slide."""
        engine.set_slide_background_color(slide_index, *bg_color)

        if top_bar:
            engine.add_bar(slide_index, 0, 0, self.W, 0.08, top_bar)
        if bottom_bar:
            engine.add_bar(slide_index, 0, self.H - 0.08, self.W, 0.08, bottom_bar)

    def _add_header(self, engine: PPTXEngine, slide_index: int,
                    title: str, subtitle: str = "",
                    accent_color: Tuple[int, int, int] = CYAN):
        """Añade header con fondo de tarjeta y título."""
        # Fondo del header
        engine.add_shape(slide_index, MSO_SHAPE.RECTANGLE,
                         0, 0, self.W, 0.88,
                         fill_color=CARD2)
        # Título
        engine.add_text_box(slide_index, title,
                            0.45, 0.1, self.W - 0.9, 0.52,
                            font_size=32, bold=True, color=accent_color)
        # Subtítulo
        if subtitle:
            engine.add_text_box(slide_index, subtitle,
                                0.45, 0.55, self.W - 0.9, 0.38,
                                font_size=14, color=LGRAY)

    def _add_card(self, engine: PPTXEngine, slide_index: int,
                  left: float, top: float, width: float, height: float,
                  border_color: Tuple[int, int, int],
                  fill_color: Tuple[int, int, int] = CARD,
                  border_width: float = 1.0):
        """Añade una tarjeta con borde de color."""
        return engine.add_shape(slide_index, MSO_SHAPE.RECTANGLE,
                              left, top, width, height,
                              fill_color=fill_color,
                              border_color=border_color,
                              border_width=border_width)

    def _add_tag(self, engine: PPTXEngine, slide_index: int,
                 left: float, top: float, width: float, height: float,
                 text: str, bg_color: Tuple[int, int, int],
                 font_size: int = 12):
        """Añade una etiqueta redondeada con texto."""
        engine.add_shape(slide_index, MSO_SHAPE.ROUNDED_RECTANGLE,
                         left, top, width, height,
                         fill_color=bg_color, rounded=True)
        engine.add_text_box(slide_index, text,
                            left, top + 0.08, width, height,
                            font_size=font_size, bold=True,
                            color=BG,  # texto oscuro sobre fondo brillante
                            alignment=PP_ALIGN.CENTER)

    def render_title_slide(self, engine: PPTXEngine, slide_index: int, data: Dict[str, Any]):
        """Slide de portada con título grande y subtítulo."""
        self._setup_slide(engine, slide_index, BG, CYAN, MAGENTA)

        # Bordes laterales decorativos
        engine.add_bar(slide_index, 0, 0, 0.08, self.H, CYAN)
        engine.add_bar(slide_index, self.W - 0.08, 0, 0.08, self.H, MAGENTA)

        # Esquinas decorativas
        engine.add_bar(slide_index, 0.35, 0.35, 0.8, 0.05, CYAN)
        engine.add_bar(slide_index, 0.35, 0.35, 0.05, 0.5, CYAN)

        # Tarjeta central
        self._add_card(engine, slide_index,
                        0.9, 1.55, 11.53, 3.8,
                        border_color=CYAN, fill_color=CARD2,
                        border_width=0.75)

        # Título principal
        title = data.get("title", "TÍTULO")
        engine.add_text_box(slide_index, title,
                            0.9, 1.65, 11.53, 2.0,
                            font_size=90, bold=True, color=CYAN,
                            alignment=PP_ALIGN.CENTER)

        # Subtítulo
        subtitle = data.get("subtitle", "")
        if subtitle:
            engine.add_text_box(slide_index, subtitle,
                                0.9, 3.55, 11.53, 0.75,
                                font_size=24, color=WHITE,
                                alignment=PP_ALIGN.CENTER)

        # Línea separadora
        engine.add_bar(slide_index, 2.2, 4.42, 8.93, 0.03, CYAN)

        # Tags inferiores (si hay bullets, los usamos como tags)
        bullets = data.get("bullets", [])
        tags = bullets if bullets else ["PitchSync", "IA", "Open Source"]
        tag_colors = [ORANGE, MAGENTA, CYAN, GREEN, YELLOW]

        tw = 1.92
        th = 0.52
        tg = 0.1
        total_tw = len(tags) * tw + (len(tags) - 1) * tg
        tsx = (self.W - total_tw) / 2
        tsy = 4.65

        for i, tag in enumerate(tags[:5]):
            lx = tsx + i * (tw + tg)
            self._add_tag(engine, slide_index, lx, tsy, tw, th,
                          tag, tag_colors[i % len(tag_colors)], 13)

        # Footer
        engine.add_text_box(slide_index,
                            "2026  ·  Universidad Nacional de La Rioja",
                            0, self.H - 0.45, self.W, 0.4,
                            font_size=12, italic=True, color=LGRAY,
                            alignment=PP_ALIGN.CENTER)

    def render_content_slide(self, engine: PPTXEngine, slide_index: int, data: Dict[str, Any]):
        """Slide de contenido con tarjeta y bullets."""
        self._setup_slide(engine, slide_index, BG, CYAN, CYAN)

        title = data.get("title", "")
        bullets = data.get("bullets", [])

        self._add_header(engine, slide_index, title, accent_color=CYAN)

        # Tarjeta de contenido
        self._add_card(engine, slide_index,
                        0.5, 1.1, 12.33, 5.8,
                        border_color=CYAN, fill_color=CARD,
                        border_width=1.0)

        # Bullets
        if bullets:
            lines = [f"• {b}" for b in bullets]
            engine.add_multiline_text(slide_index, lines,
                                      0.8, 1.4, 11.7, 5.2,
                                      font_size=18, color=WHITE,
                                      line_spacing=1.8)

    def render_section_divider(self, engine: PPTXEngine, slide_index: int, data: Dict[str, Any]):
        """Slide de transición con título grande centrado."""
        self._setup_slide(engine, slide_index, CARD2, GREEN, GREEN)

        title = data.get("title", "SECCIÓN")
        engine.add_text_box(slide_index, title,
                            0.5, 2.5, 12.33, 2.0,
                            font_size=72, bold=True, color=GREEN,
                            alignment=PP_ALIGN.CENTER)

        # Línea decorativa
        engine.add_bar(slide_index, 3.0, 4.6, 7.33, 0.04, GREEN)

    def render_image_slide(self, engine: PPTXEngine, slide_index: int, data: Dict[str, Any]):
        """Slide con título y placeholder de imagen."""
        self._setup_slide(engine, slide_index, BG, MAGENTA, MAGENTA)

        title = data.get("title", "")
        self._add_header(engine, slide_index, title, accent_color=MAGENTA)

        # Placeholder de imagen con borde
        img_prompt = data.get("image_prompt", "🎨 AI IMAGE")
        self._add_card(engine, slide_index,
                        1.0, 1.2, 11.33, 5.5,
                        border_color=MAGENTA, fill_color=CARD2,
                        border_width=1.5)

        engine.add_text_box(slide_index, f"🎨 AI IMAGE\n{img_prompt[:100]}...",
                            1.0, 3.5, 11.33, 1.0,
                            font_size=16, color=MAGENTA,
                            alignment=PP_ALIGN.CENTER)

    def render_split_slide(self, engine: PPTXEngine, slide_index: int, data: Dict[str, Any]):
        """Slide dividida: contenido a la izquierda, placeholder a la derecha."""
        self._setup_slide(engine, slide_index, BG, ORANGE, ORANGE)

        title = data.get("title", "")
        bullets = data.get("bullets", [])

        self._add_header(engine, slide_index, title, accent_color=ORANGE)

        # Panel izquierdo (contenido)
        self._add_card(engine, slide_index,
                        0.5, 1.1, 6.0, 5.8,
                        border_color=ORANGE, fill_color=CARD,
                        border_width=1.0)

        if bullets:
            lines = [f"• {b}" for b in bullets]
            engine.add_multiline_text(slide_index, lines,
                                      0.8, 1.4, 5.5, 5.2,
                                      font_size=16, color=WHITE,
                                      line_spacing=1.6)

        # Panel derecho (imagen/placeholder)
        self._add_card(engine, slide_index,
                        6.8, 1.1, 5.8, 5.8,
                        border_color=ORANGE, fill_color=CARD2,
                        border_width=1.0)

        engine.add_text_box(slide_index, "🖼️ IMAGEN\n(AI o importada)",
                            6.8, 3.5, 5.8, 1.0,
                            font_size=16, color=ORANGE,
                            alignment=PP_ALIGN.CENTER)