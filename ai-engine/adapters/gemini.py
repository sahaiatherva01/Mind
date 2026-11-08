"""
Google Gemini AI Provider Adapter
Uses structured JSON schema output mode with Gemini 1.5 Flash / Pro.
"""
import json
import uuid
import httpx
from typing import List, Optional
from ai_engine.adapters.base import BaseAIProvider
from ai_engine.schemas.question import CanonicalQuestion, GenerationRequestSpec
from backend.app.core.config import settings
from backend.app.core.errors import ValidationException


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.flash_model = settings.GEMINI_FLASH_MODEL
        self.pro_model = settings.GEMINI_PRO_MODEL

    async def generate_questions(
        self,
        spec: GenerationRequestSpec,
        prompt_template: str,
    ) -> List[CanonicalQuestion]:
        if not self.api_key:
            raise ValidationException("Gemini API key is not configured. Please set GEMINI_API_KEY or use AI_PROVIDER=mock.")

        # Prepare system prompt and user input
        system_instruction = (
            "You are an expert ICSE and ISC Board Exam assessment author for secondary and senior secondary schools. "
            "Output must be strictly valid JSON matching the CanonicalQuestion schema. "
            "Never invent facts. Always provide marking schemes and rationales for teachers."
        )

        user_content = (
            f"Generate an academic {spec.output_type} with exactly {spec.question_count} questions for total {spec.total_marks} marks.\n"
            f"Board: {spec.board}\n"
            f"Chapter: {spec.chapter}\n"
            f"Topics: {', '.join(spec.topics)}\n"
            f"Question Types: {', '.join(spec.question_types)}\n"
            f"Difficulty Distribution: {json.dumps(spec.difficulty_distribution)}\n"
            f"Instructions: {spec.instructions or 'None'}\n"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.flash_model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": user_content}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.4,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise ValidationException(f"Gemini API returned error {resp.status_code}: {resp.text}")

            result = resp.json()
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(raw_text)

            # Support either top-level list or object with "questions" key
            items = parsed_json if isinstance(parsed_json, list) else parsed_json.get("questions", [])

            questions: List[CanonicalQuestion] = []
            for item in items:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                questions.append(CanonicalQuestion.model_validate(item))

            return questions

    async def regenerate_single_question(
        self,
        existing_question: CanonicalQuestion,
        feedback: str,
    ) -> CanonicalQuestion:
        if not self.api_key:
            # Fallback
            new_q = existing_question.model_copy(deep=True)
            new_q.id = str(uuid.uuid4())
            new_q.prompt = f"{existing_question.prompt} ({feedback})"
            new_q.version += 1
            return new_q

        # Call Gemini for single item
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.flash_model}:generateContent?key={self.api_key}"
        prompt = (
            f"Revise the following question based on teacher feedback: '{feedback}'.\n"
            f"Existing question: {existing_question.model_dump_json()}\n"
            "Return a single updated CanonicalQuestion JSON object."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise ValidationException(f"Gemini API error during item regeneration: {resp.text}")

            parsed = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
            parsed["id"] = str(uuid.uuid4())
            parsed["version"] = existing_question.version + 1
            return CanonicalQuestion.model_validate(parsed)

