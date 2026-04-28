"""
processors/ai_content_processor.py — Procesador de Generación de Contenido IA
Multi-proveedor: detecta el proveedor según el modelo seleccionado.
"""

from core.ai_client import AIClientFactory
from core.content_orchestrator import ContentOrchestrator
from .base import BaseProcessor, ProcessingContext

class AIContentProcessor(BaseProcessor):
    """
    Procesador que genera la estructura completa de la presentación vía IA.
    Soporta OpenRouter, Groq, Claude y Moonshot directamente.
    """

    name = "AI Content Generator"
    priority = 5  # Primero

    def __init__(self, api_key: str = None):
        # api_key se mantiene por compatibilidad, pero ahora se detecta automáticamente
        self.api_key = api_key
        self._client = None
        self._orchestrator = None

    def _get_orchestrator(self, model_id: str = None) -> ContentOrchestrator:
        """
        Crea el orquestador con el cliente correcto según el modelo.
        """
        # El orquestador ahora maneja la creación del cliente internamente
        # Creamos un cliente dummy inicial, el orquestador lo reemplazará
        client = AIClientFactory.create("openrouter", self.api_key)
        return ContentOrchestrator(client)

    async def process(self, ctx: ProcessingContext) -> None:
        model_id = ctx.metadata.get('model_id')
        ctx.emit(f"🤖 Generando contenido con modelo: {model_id or 'default'}")

        orchestrator = self._get_orchestrator(model_id)

        result = await orchestrator.generate_from_prompt(
            prompt=ctx.metadata.get("prompt", ""),
            input_type=ctx.metadata.get("input_type", "summary"),
            model_id=model_id,
            context_text=ctx.notes_text or None
        )

        ctx.generated_structure = result
        ctx.metadata["model_used"] = result.get("_meta", {}).get("model_name")
        ctx.metadata["provider_used"] = result.get("_meta", {}).get("provider")
        ctx.metadata["slide_count"] = result.get("_meta", {}).get("slide_count")

        ctx.emit(f"✅ Estructura generada: {result.get('title')} ({len(result.get('slides', []))} slides)")