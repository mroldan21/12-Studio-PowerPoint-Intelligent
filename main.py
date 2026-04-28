"""
main.py — PPTX Studio Intelligent Edition
FastAPI entry point con soporte multi-proveedor y multi-tema.
"""

import io
import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.pptx_engine import PPTXEngine
from core.ai_client import AIClientFactory
from core.content_orchestrator import ContentOrchestrator
from core.slide_designer import SlideDesigner
from core.themes import ThemeRegistry
from processors.base import ProcessingContext
from processors.ai_content_processor import AIContentProcessor
from processors.slide_design_processor import SlideDesignProcessor
from processors.image_processor import ImageProcessor
from processors.notes_processor import NotesProcessor

app = FastAPI(
    title="PPTX Studio — Intelligent Edition",
    description="Genera presentaciones completas con IA. Multi-proveedor, multi-tema.",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar temas al iniciar
ThemeRegistry.load_json_themes()

# Servir archivos estáticos
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PPTX Studio Intelligent Edition API", "version": "2.2.0"}

@app.get("/health")
async def health():
    config_path = Path(__file__).parent / "config" / "models_config.json"
    models = []
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            models = config.get("models", [])

    api_status = {
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "claude": bool(os.getenv("ANTHROPIC_API_KEY")),
        "moonshot": bool(os.getenv("MOONSHOT_API_KEY")),
    }

    return {
        "status": "online",
        "service": "PPTX Studio Intelligent Edition",
        "version": "2.2.0",
        "available_models": len(models),
        "api_providers_configured": api_status,
        "models": [{"id": m["id"], "name": m["name"], "provider": m.get("provider", "openrouter")} for m in models]
    }

@app.get("/models")
async def list_models():
    config_path = Path(__file__).parent / "config" / "models_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/themes")
async def list_themes():
    """Lista todos los temas disponibles."""
    return {
        "themes": ThemeRegistry.list_themes(),
        "note": "Usa 'template:<ruta>' para plantillas PPTX personalizadas"
    }

@app.post("/generate")
async def generate_presentation(
    prompt: str = Form(...),
    input_type: str = Form("summary"),
    model_id: Optional[str] = Form(None),
    theme: str = Form("pitchsync_cyber"),  # Default al nuevo tema cyberpunk
    template_file: Optional[UploadFile] = File(None),  # Plantilla PPTX opcional
    include_images: bool = Form(True),
    filename: str = Form("presentation.pptx")
):
    """
    Endpoint principal de generación.
    
    - theme: Nombre del tema (pitchsync_dark, pitchsync_cyber, etc.)
    - template_file: PPTX de plantilla personalizada (opcional, sobrescribe theme)
    """
    try:
        engine = PPTXEngine()
        engine.create_blank(slide_count=1)

        # Si se sube plantilla, usar TemplateTheme
        if template_file and template_file.filename:
            template_bytes = await template_file.read()
            # Guardar temporalmente
            temp_path = Path("/tmp") / f"template_{template_file.filename}"
            temp_path.write_bytes(template_bytes)
            from core.themes import TemplateTheme
            custom_theme = TemplateTheme(str(temp_path))
            ThemeRegistry.register(f"custom_{template_file.filename}", custom_theme)
            theme = f"custom_{template_file.filename}"

        ctx = ProcessingContext()
        ctx.engine = engine
        ctx.metadata = {
            "prompt": prompt,
            "input_type": input_type,
            "model_id": model_id,
            "theme": theme,
            "include_images": include_images
        }

        processors = [
            AIContentProcessor(),
            SlideDesignProcessor(theme),
        ]

        if include_images:
            processors.append(ImageProcessor())

        processors.append(NotesProcessor())

        for processor in processors:
            ctx.emit(f"▶ Ejecutando: {processor.name}")
            await processor.process(ctx)
            ctx.emit(f"✓ Completado: {processor.name}")

        output = io.BytesIO()
        engine.save(output)
        output.seek(0)

        safe_name = filename if filename.endswith(".pptx") else f"{filename}.pptx"

        response_headers = {
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Model-Used": ctx.metadata.get("model_used", "unknown"),
            "X-Provider-Used": ctx.metadata.get("provider_used", "unknown"),
            "X-Theme-Used": theme,
            "X-Slide-Count": str(ctx.metadata.get("slide_count", 0)),
            "X-Processing-Log": json.dumps(ctx.log)
        }

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers=response_headers
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/json")
async def generate_presentation_json(
    prompt: str = Form(...),
    input_type: str = Form("summary"),
    model_id: Optional[str] = Form(None)
):
    try:
        orchestrator = ContentOrchestrator(
            AIClientFactory.create("openrouter")
        )
        result = await orchestrator.generate_from_prompt(
            prompt=prompt,
            input_type=input_type,
            model_id=model_id
        )
        return JSONResponse({"success": True, "structure": result})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)