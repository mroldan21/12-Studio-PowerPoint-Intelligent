"""
core/ai_client.py — Cliente unificado multi-proveedor
Soporta: OpenRouter, Groq, Claude (Anthropic), Moonshot, Gemini (Google)
"""

import os
import json
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class AIResponse:
    content: str
    model_used: str
    tokens_used: int
    finish_reason: str
    raw_response: Dict[str, Any]


class BaseAIClient(ABC):
    """Interfaz base para todos los clientes de IA."""

    @abstractmethod
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> AIResponse:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise


class OpenRouterClient(BaseAIClient):
    """Cliente para la API de OpenRouter."""

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
    ) -> AIResponse:
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

                return AIResponse(
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
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

        return self._parse_json_response(response.content)


class GroqClient(BaseAIClient):
    """Cliente directo para la API de Groq."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurada")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> AIResponse:
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
                    raise Exception(f"Groq error {response.status}: {error_text}")

                data = await response.json()
                choice = data["choices"][0]

                return AIResponse(
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
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

        return self._parse_json_response(response.content)


class ClaudeClient(BaseAIClient):
    """Cliente directo para la API de Anthropic (Claude)."""

    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")

        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> AIResponse:
        system_msg = None
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        payload = {
            "model": model,
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096
        }
        if system_msg:
            payload["system"] = system_msg

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.BASE_URL}/messages",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Claude error {response.status}: {error_text}")

                data = await response.json()
                content_block = data["content"][0]

                return AIResponse(
                    content=content_block["text"],
                    model_used=data.get("model", model),
                    tokens_used=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
                    finish_reason=data.get("stop_reason", "unknown"),
                    raw_response=data
                )

    async def generate_structured(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_completion(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        return self._parse_json_response(response.content)


class MoonshotClient(BaseAIClient):
    """Cliente directo para la API de Moonshot (Kimi)."""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY no configurada")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> AIResponse:
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
                    raise Exception(f"Moonshot error {response.status}: {error_text}")

                data = await response.json()
                choice = data["choices"][0]

                return AIResponse(
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
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

        return self._parse_json_response(response.content)


class GeminiClient(BaseAIClient):
    """Cliente directo para la API de Google Gemini."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY no configurada")

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> AIResponse:
        # Gemini usa formato diferente: contents en lugar de messages
        contents = []
        system_instruction = None

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = {"parts": [{"text": msg["content"]}]}
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini error {response.status}: {error_text}")

                data = await response.json()
                candidate = data["candidates"][0]
                content = candidate["content"]["parts"][0]["text"]

                # Estimar tokens (Gemini no siempre devuelve usage)
                tokens_used = data.get("usageMetadata", {}).get("totalTokenCount", 0)

                return AIResponse(
                    content=content,
                    model_used=model,
                    tokens_used=tokens_used,
                    finish_reason=candidate.get("finishReason", "unknown"),
                    raw_response=data
                )

    async def generate_structured(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await self.chat_completion(
            model=model,
            messages=messages,
            temperature=0.5
        )

        return self._parse_json_response(response.content)


# ── FÁBRICA DE CLIENTES ───────────────────────────────────────────────────

class AIClientFactory:
    """
    Fábrica que crea el cliente apropiado según el provider del modelo.
    """

    PROVIDERS = {
        "openrouter": OpenRouterClient,
        "groq": GroqClient,
        "claude": ClaudeClient,
        "anthropic": ClaudeClient,
        "moonshot": MoonshotClient,
        "gemini": GeminiClient,
        "google": GeminiClient,
    }

    @classmethod
    def create(cls, provider: str, api_key: Optional[str] = None) -> BaseAIClient:
        provider = provider.lower().strip()
        client_class = cls.PROVIDERS.get(provider)
        if not client_class:
            raise ValueError(f"Proveedor '{provider}' no soportado. Disponibles: {list(cls.PROVIDERS.keys())}")
        return client_class(api_key)

    @classmethod
    def create_for_model(cls, model_id: str, models_config: List[Dict]) -> BaseAIClient:
        """
        Busca el modelo en la config y crea el cliente correspondiente.
        Si no encuentra provider, asume OpenRouter por compatibilidad.
        """
        for model in models_config:
            if model["id"] == model_id:
                provider = model.get("provider", "openrouter")
                return cls.create(provider)
        return cls.create("openrouter")