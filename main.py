"""
main.py — PPTX Studio Intelligent Edition
FastAPI entry point con endpoints para generación inteligente.
"""

import io
import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.pptx_engine import PPTXEngine
from core.ai_client import OpenRouterClient
from core.content_orchestrator import ContentOrchestrator
from core.slide_designer import SlideDesigner
from processors.base import ProcessingContext
from processors.ai_content_processor import AIContentProcessor
from processors.slide_design_processor import SlideDesignProcessor
from processors.image_processor import ImageProcessor
from processors.notes_processor import NotesProcessor

app = FastAPI(
    title="PPTX Studio — Intelligent Edition",
    description="Genera presentaciones completas con IA vía OpenRouter",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (frontend)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Sirve el frontend SPA."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PPTX Studio Intelligent Edition API", "version": "2.0.0"}

@app.get("/health")
async def health():
    """Estado del servicio y modelos disponibles."""
    config_path = Path(__file__).parent / "config" / "models_config.json"
    models = []
    if config_path.exists():
        with open(config_path) as f:
            models = json.load(f).get("models", [])
    
    return {
        "status": "online",
        "service": "PPTX Studio Intelligent Edition",
        "version": "2.0.0",
        "available_models": len(models),
        "models": [{"id": m["id"], "name": m["name"]} for m in models]
    }

@app.get("/models")
async def list_models():
    """Lista todos los modelos configurados."""
    config_path = Path(__file__).parent / "config" / "models_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/generate")
async def generate_presentation(
    prompt: str = Form(...),
    input_type: str = Form("summary"),  # summary, extensive_notes, research, pptx_import
    model_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    theme: str = Form("pitchsync_dark"),
    include_images: bool = Form(True),
    filename: str = Form("presentation.pptx")
):
    """
    Endpoint principal de generación inteligente.
    
    - prompt: Tema o contenido para la presentación
    - input_type: Tipo de entrada (determina el system prompt)
    - model_id: Modelo OpenRouter a usar (opcional, usa recomendado si no se especifica)
    - file: PPTX existente (solo para input_type=pptx_import)
    - theme: Tema visual a aplicar
    - include_images: Incluir placeholders de imagen IA
    """
    try:
        # 1. Inicializar engine
        engine = PPTXEngine()
        engine.create_blank(slide_count=1)  # Mínimo, se expandirá según necesidad
        
        # 2. Preparar contexto
        ctx = ProcessingContext()
        ctx.engine = engine
        ctx.metadata = {
            "prompt": prompt,
            "input_type": input_type,
            "model_id": model_id,
            "theme": theme,
            "include_images": include_images
        }
        
        # Si hay archivo PPTX, extraer contenido para contexto
        if file and file.filename:
            content = await file.read()
            # Guardar temporalmente para extraer texto (simplificado)
            ctx.notes_text = f"PPTX importado: {file.filename}"
            engine.load(io.BytesIO(content))
            ctx.metadata["imported_file"] = file.filename
        
        # 3. Ejecutar pipeline
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        processors = [
            AIContentProcessor(api_key),
            SlideDesignProcessor(theme),
        ]
        
        if include_images:
            processors.append(ImageProcessor())
        
        processors.append(NotesProcessor())
        
        for processor in processors:
            ctx.emit(f"▶ Ejecutando: {processor.name}")
            await processor.process(ctx)
            ctx.emit(f"✓ Completado: {processor.name}")
        
        # 4. Generar archivo de salida
        output = io.BytesIO()
        engine.save(output)
        output.seek(0)
        
        safe_name = filename if filename.endswith(".pptx") else f"{filename}.pptx"
        
        # 5. Preparar respuesta con metadatos
        response_headers = {
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "X-Model-Used": ctx.metadata.get("model_used", "unknown"),
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
    """
    Devuelve solo la estructura JSON generada (sin crear PPTX).
    Útil para preview o debugging.
    """
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        client = OpenRouterClient(api_key)
        orchestrator = ContentOrchestrator(client)
        
        result = await orchestrator.generate_from_prompt(
            prompt=prompt,
            input_type=input_type,
            model_id=model_id
        )
        
        return JSONResponse({
            "success": True,
            "structure": result
        })
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )