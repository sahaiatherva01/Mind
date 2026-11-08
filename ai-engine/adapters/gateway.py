"""
AI Gateway: Provider Router, Schema Validation & Domain Integrity Verification
"""
from typing import List, Tuple
from ai_engine.adapters.base import BaseAIProvider
from ai_engine.adapters.mock import MockAIProvider
from ai_engine.adapters.gemini import GeminiProvider
from ai_engine.schemas.question import CanonicalQuestion, GenerationRequestSpec
from backend.app.core.config import settings
from backend.app.core.errors import ValidationException


class AIGateway:
    def __init__(self, provider_name: str = settings.AI_PROVIDER):
        self.provider_name = provider_name.lower()
        if self.provider_name == "gemini":
            self.provider: BaseAIProvider = GeminiProvider()
        else:
            self.provider = MockAIProvider()

    def validate_domain_rules(
        self,
        questions: List[CanonicalQuestion],
        spec: GenerationRequestSpec,
    ) -> Tuple[List[CanonicalQuestion], List[str]]:
        """
        Validates:
        1. Total marks match requested total
        2. MCQ option completeness (at least 2 options, distinct texts, valid answer_keys)
        3. Flags unverified factual assertions
        """
        warnings: List[str] = []
        total_marks = sum(q.marks for q in questions)

        if total_marks != spec.total_marks:
            # Auto-balance residual difference on the highest-weight item
            diff = spec.total_marks - total_marks
            if questions:
                questions[0].marks += diff
                warnings.append(f"Auto-adjusted item 1 mark weight by {diff} to equal total {spec.total_marks} marks.")

        for idx, q in enumerate(questions, start=1):
            # Check MCQ integrity
            if q.type in ("mcq", "multiple_select", "assertion_reason"):
                if not q.options or len(q.options) < 2:
                    raise ValidationException(f"Question #{idx} ({q.type}) must have at least 2 options.")

                option_ids = [opt.id for opt in q.options]
                if len(option_ids) != len(set(option_ids)):
                    raise ValidationException(f"Question #{idx} has duplicate option identifiers.")

                option_texts = [opt.text.strip().lower() for opt in q.options]
                if len(option_texts) != len(set(option_texts)):
                    raise ValidationException(f"Question #{idx} has duplicate option text choices.")

                # Verify correct answer exists
                valid_keys = set(option_ids)
                if q.answer_keys:
                    for key in q.answer_keys:
                        if key not in valid_keys:
                            raise ValidationException(
                                f"Question #{idx} answer key '{key}' does not match any valid option ({valid_keys})."
                            )

            # Detect speculative claims
            suspicious_words = ["allegedly", "rumored", "unverified", "disputed"]
            if any(w in q.prompt.lower() for w in suspicious_words):
                q.flagged_uncertain = True
                warnings.append(f"Question #{idx} flagged for teacher review due to potentially speculative phrasing.")

        return questions, warnings

    async def generate_draft(
        self,
        spec: GenerationRequestSpec,
        prompt_version: str = "v1.0",
    ) -> Tuple[List[CanonicalQuestion], List[str]]:
        raw_questions = await self.provider.generate_questions(spec, prompt_template=prompt_version)
        validated_questions, warnings = self.validate_domain_rules(raw_questions, spec)
        return validated_questions, warnings

    async def regenerate_item(
        self,
        question: CanonicalQuestion,
        feedback: str,
    ) -> CanonicalQuestion:
        return await self.provider.regenerate_single_question(question, feedback)
