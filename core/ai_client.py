"""
core/ai_client.py — Cliente unificado de OpenRouter
"""

import os
import json
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class OpenRouterResponse:
    content: str
    model_used: str
    tokens_used: int
    finish_reason: str
    raw_response: Dict[str, Any]

class OpenRouterClient:
    """
    Cliente para la API de OpenRouter.
    Requiere variable de entorno OPENROUTER_API_KEY.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pptx-studio.local",
            "X-Title": "PPTX Studio Intelligent Edition"
        }
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> OpenRouterResponse:
        """
        Realiza una llamada de chat completion a OpenRouter.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter error {response.status}: {error_text}")
                
                data = await response.json()
                choice = data["choices"][0]
                
                return OpenRouterResponse(
                    content=choice["message"]["content"],
                    model_used=data.get("model", model),
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                    finish_reason=choice.get("finish_reason", "unknown"),
                    raw_response=data
                )
    
    async def generate_structured(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera contenido estructurado (JSON) usando response_format.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(
            model=model,
            messages=messages,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback: intentar extraer JSON del texto
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise