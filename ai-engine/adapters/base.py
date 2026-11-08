"""
Base AI Provider Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ai_engine.schemas.question import CanonicalQuestion, GenerationRequestSpec


class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_questions(
        self,
        spec: GenerationRequestSpec,
        prompt_template: str,
    ) -> List[CanonicalQuestion]:
        """Generates a structured list of canonical questions matching the request specification."""
        pass

    @abstractmethod
    async def regenerate_single_question(
        self,
        existing_question: CanonicalQuestion,
        feedback: str,
    ) -> CanonicalQuestion:
        """Regenerates a single item without losing teacher context."""
        pass
