"""
Subjective Evaluation Assistant Agent — Mind V2 (Agent Track A3)
LangGraph StateGraph workflow for subjective grading suggestions with rubric matching,
step-by-step scoring breakdown, and constructive feedback.
Teacher approval is mandatory: AI output is strictly an advisory suggestion.
"""
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
import re

from backend.app.core.config import settings
from backend.app.content.models import Question
from backend.app.assessments.models import StudentResponse, AssessmentItem


class EvaluationState(TypedDict, total=False):
    response_id: str
    question_prompt: str
    student_answer: str
    model_answer: str
    rubric_steps: List[str]
    max_marks: float
    rubric_matches: List[Dict[str, Any]]
    suggested_score: float
    teacher_feedback_note: str
    confidence_score: float


class RubricMatcherNode:
    """Matches student text against required rubric concepts, keywords, and derivations."""

    @staticmethod
    def run(state: EvaluationState) -> Dict[str, Any]:
        student_text = state.get("student_answer", "").strip()
        model_answer = state.get("model_answer", "").strip()
        rubric_steps = state.get("rubric_steps", [])
        max_marks = state.get("max_marks", 1.0)

        if not rubric_steps and model_answer:
            # Derive steps from model answer sentences
            rubric_steps = [s.strip() for s in model_answer.split(".") if len(s.strip()) > 5]

        if not rubric_steps:
            rubric_steps = ["Identification of core principle", "Analytical explanation & derivation"]

        matches = []
        marks_per_step = max_marks / len(rubric_steps) if rubric_steps else max_marks

        for step in rubric_steps:
            # Extract keywords from step
            keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", step)]
            matched_keywords = [kw for kw in keywords if kw in student_text.lower()]
            match_ratio = len(matched_keywords) / len(keywords) if keywords else 0.5

            if match_ratio >= 0.5 or (len(student_text) > 10 and len(keywords) == 0):
                matches.append({
                    "step_criterion": step,
                    "status": "met",
                    "awarded_mark": round(marks_per_step, 1),
                    "max_step_mark": round(marks_per_step, 1),
                    "rationale": f"Key concepts identified: {', '.join(matched_keywords[:3]) or 'criteria addressed'}",
                })
            elif match_ratio > 0.2:
                matches.append({
                    "step_criterion": step,
                    "status": "partial",
                    "awarded_mark": round(marks_per_step * 0.5, 1),
                    "max_step_mark": round(marks_per_step, 1),
                    "rationale": "Partially addressed; incomplete explanation or missing terminology.",
                })
            else:
                matches.append({
                    "step_criterion": step,
                    "status": "missing",
                    "awarded_mark": 0.0,
                    "max_step_mark": round(marks_per_step, 1),
                    "rationale": "Step omitted or inadequate conceptual coverage in response.",
                })

        return {"rubric_matches": matches}


class ScoringCalibratorNode:
    """Calculates final suggested score ensuring 0 <= score <= max_marks."""

    @staticmethod
    def run(state: EvaluationState) -> Dict[str, Any]:
        rubric_matches = state.get("rubric_matches", [])
        max_marks = state.get("max_marks", 1.0)

        raw_score = sum(m["awarded_mark"] for m in rubric_matches)
        # Cap strictly between 0 and max_marks
        calibrated_score = max(0.0, min(float(max_marks), round(raw_score, 1)))

        confidence = 0.88 if len(rubric_matches) > 1 else 0.75
        return {
            "suggested_score": calibrated_score,
            "confidence_score": confidence,
        }


class FeedbackSynthesizerNode:
    """Synthesizes structured feedback note highlighting strengths and missing steps."""

    @staticmethod
    def run(state: EvaluationState) -> Dict[str, Any]:
        rubric_matches = state.get("rubric_matches", [])
        score = state.get("suggested_score", 0.0)
        max_marks = state.get("max_marks", 1.0)

        met_steps = [m["step_criterion"] for m in rubric_matches if m["status"] == "met"]
        missing_steps = [m["step_criterion"] for m in rubric_matches if m["status"] in ("missing", "partial")]

        feedback_parts = []
        if met_steps:
            feedback_parts.append(f"Demonstrated good understanding of: {met_steps[0]}.")
        if missing_steps:
            feedback_parts.append(f"Needs improvement on: {missing_steps[0]}.")
        else:
            feedback_parts.append("Comprehensive and well-structured response.")

        feedback_note = " ".join(feedback_parts)
        return {"teacher_feedback_note": feedback_note}


def create_evaluation_assistant_graph():
    graph = StateGraph(EvaluationState)
    graph.add_node("rubric_matcher", RubricMatcherNode.run)
    graph.add_node("scoring_calibrator", ScoringCalibratorNode.run)
    graph.add_node("feedback_synthesizer", FeedbackSynthesizerNode.run)

    graph.set_entry_point("rubric_matcher")
    graph.add_edge("rubric_matcher", "scoring_calibrator")
    graph.add_edge("scoring_calibrator", "feedback_synthesizer")
    graph.add_edge("feedback_synthesizer", END)

    return graph.compile()


evaluation_assistant_pipeline = create_evaluation_assistant_graph()


class EvaluatorAgent:
    """Main interface for subjective response evaluation assistance."""

    @staticmethod
    async def evaluate_response(
        response_id: str,
        question: Question,
        item: AssessmentItem,
        student_response: StudentResponse,
    ) -> Dict[str, Any]:
        student_ans = student_response.answer_json.get("text") or str(student_response.answer_json)
        ans_data = question.answer_data or {}
        model_answer = ans_data.get("model_answer") or ans_data.get("expected_answer") or ""
        marking_scheme = ans_data.get("marking_scheme") or ans_data.get("rubric_steps") or []
        max_marks = float(item.marks_override or question.marks or 1.0)

        initial_state: EvaluationState = {
            "response_id": response_id,
            "question_prompt": question.prompt,
            "student_answer": student_ans,
            "model_answer": model_answer,
            "rubric_steps": marking_scheme,
            "max_marks": max_marks,
        }

        # Run LangGraph pipeline
        result = await evaluation_assistant_pipeline.ainvoke(initial_state)

        return {
            "response_id": response_id,
            "question_prompt": question.prompt,
            "student_answer_text": student_ans,
            "model_answer": model_answer,
            "max_marks": max_marks,
            "suggested_score": result.get("suggested_score", 0.0),
            "step_breakdown": result.get("rubric_matches", []),
            "teacher_feedback_note": result.get("teacher_feedback_note", ""),
            "confidence_score": result.get("confidence_score", 0.85),
        }
