"""
processors/base.py — Clase base para todos los procesadores
"""

from abc import ABC, abstractmethod
from typing import Any

class ProcessingContext:
    """Contexto compartido del pipeline."""
    
    def __init__(self):
        self.engine: Any = None  # PPTXEngine
        self.notes_text: str = ""
        self.separator: str = "---"
        self.image_directives: list = []
        self.log: list = []
        self.metadata: dict = {}
        self.generated_structure: dict = {}  # NUEVO: estructura JSON de IA
        self.ai_response: Any = None  # NUEVO: respuesta del modelo
    
    def emit(self, message: str):
        self.log.append(message)
        print(f"[Pipeline] {message}")

class BaseProcessor(ABC):
    """Procesador base abstracto."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    def priority(self) -> int:
        return 50
    
    @abstractmethod
    async def process(self, ctx: ProcessingContext) -> None:
        pass