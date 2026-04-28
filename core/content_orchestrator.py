"""
core/content_orchestrator.py — Orquestador de Generación de Contenido
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from .ai_client import OpenRouterClient

class ContentOrchestrator:
    """
    Orquesta el flujo completo: Prompt → Estructura JSON → Datos procesados.
    Implementa el patrón Strategy para los diferentes tipos de entrada.
    """
    
    def __init__(self, ai_client: OpenRouterClient):
        self.ai_client = ai_client
        self.models_config = self._load_models_config()
    
    def _load_models_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "models_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict]:
        for model in self.models_config["models"]:
            if model["id"] == model_id:
                return model
        return None
    
    def get_recommended_model(self, task_type: str) -> str:
        """Devuelve el primer modelo recomendado para el tipo de tarea."""
        for model in self.models_config["models"]:
            if task_type in model.get("recommended_for", []):
                return model["id"]
        return self.models_config["default_model"]
    
    # ── SYSTEM PROMPTS POR TIPO DE ENTRADA ─────────────────────────────────
    
    SYSTEM_PROMPTS = {
        "summary": """Eres un experto en diseño de presentaciones. Tu tarea es convertir un resumen en una estructura de diapositivas profesional.
Genera un JSON con esta estructura exacta:
{
  "title": "Título de la presentación",
  "subtitle": "Subtítulo opcional",
  "slides": [
    {
      "type": "title_slide|content_slide|split_slide|image_slide|section_divider",
      "title": "Título de la diapositiva",
      "bullets": ["punto clave 1", "punto clave 2", "punto clave 3"],
      "notes": "Notas detalladas para el orador (2-3 frases)",
      "image_prompt": "Descripción detallada para generar una imagen relevante (solo para image_slide)"
    }
  ]
}
REGLAS:
- Máximo 8-10 diapositivas para un resumen
- Cada bullet debe ser conciso (máximo 15 palabras)
- Las notas deben expandir el contenido para el orador
- image_prompt solo en slides de tipo image_slide""",
        
        "extensive_notes": """Eres un experto en diseño de presentaciones académicas. Convierte apuntes extensos en diapositivas estructuradas.
Genera un JSON con esta estructura exacta:
{
  "title": "Título de la presentación",
  "subtitle": "Subtítulo",
  "slides": [
    {
      "type": "title_slide|content_slide|split_slide|image_slide|section_divider",
      "title": "Título de la diapositiva",
      "bullets": ["punto clave 1", "punto clave 2"],
      "notes": "Notas detalladas para el orador (3-5 frases explicativas)",
      "image_prompt": "Descripción para imagen (solo image_slide)"
    }
  ]
}
REGLAS:
- Máximo 12-15 diapositivas para apuntes extensos
- Organiza en secciones con section_divider
- Bullets concisos, notas extensas
- Incluye al menos 2 image_slide para ilustrar conceptos clave""",
        
        "research": """Eres un investigador académico experto en crear presentaciones de investigación. Genera una estructura rigurosa.
Genera un JSON con esta estructura exacta:
{
  "title": "Título de la investigación",
  "subtitle": "Autores / Institución",
  "slides": [
    {
      "type": "title_slide|content_slide|split_slide|image_slide|section_divider",
      "title": "Título de la diapositiva",
      "bullets": ["punto clave 1", "punto clave 2"],
      "notes": "Notas académicas detalladas con citas y contexto",
      "image_prompt": "Descripción para imagen científica/diagrama"
    }
  ]
}
REGLAS:
- Estructura académica: Introducción, Metodología, Resultados, Conclusión
- Máximo 15 diapositivas
- Notas con nivel de detalle para defensa de tesis
- Incluye diagramas y figuras donde sea relevante""",
        
        "pptx_import": """Eres un experto en análisis y mejora de presentaciones. Analiza el contenido de un PPTX existente y genera una versión mejorada.
Genera un JSON con esta estructura exacta:
{
  "title": "Título mejorado",
  "subtitle": "Subtítulo",
  "slides": [
    {
      "type": "title_slide|content_slide|split_slide|image_slide|section_divider",
      "title": "Título mejorado de la diapositiva",
      "bullets": ["punto mejorado 1", "punto mejorado 2"],
      "notes": "Notas mejoradas y expandidas",
      "image_prompt": "Descripción para nueva imagen (solo image_slide)"
    }
  ]
}
REGLAS:
- Mejora los títulos para que sean más impactantes
- Expande bullets con información más relevante
- Añade notas de orador donde no existan
- Sugiere nuevas imágenes para slides sin contenido visual"""
    }
    
    async def generate_from_prompt(
        self,
        prompt: str,
        input_type: str,  # "summary", "extensive_notes", "research", "pptx_import"
        model_id: Optional[str] = None,
        context_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orquesta la generación completa de la estructura de la presentación.
        """
        # Seleccionar modelo
        if not model_id:
            model_id = self.get_recommended_model(input_type)
        
        model = self.get_model_by_id(model_id)
        if not model:
            raise ValueError(f"Modelo {model_id} no encontrado en configuración")
        
        # Construir prompt de usuario
        user_prompt = f"""CREAR PRESENTACIÓN: {prompt}

"""
        if context_text:
            user_prompt += f"""CONTEXTO ADICIONAL:
{context_text}

"""
        user_prompt += """Genera la estructura completa de la presentación en formato JSON según las instrucciones del sistema."""
        
        # Llamar a OpenRouter
        system_prompt = self.SYSTEM_PROMPTS.get(
            input_type, 
            self.SYSTEM_PROMPTS["summary"]
        )
        
        result = await self.ai_client.generate_structured(
            model=model_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema={"type": "object"}  # OpenRouter inferirá del system prompt
        )
        
        # Enriquecer resultado con metadatos
        result["_meta"] = {
            "model_used": model_id,
            "model_name": model["name"],
            "input_type": input_type,
            "slide_count": len(result.get("slides", []))
        }
        
        return result