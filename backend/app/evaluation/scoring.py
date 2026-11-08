"""
Deterministic Server-Side Scoring Engine for Objective Questions
Supports: MCQ, Multiple Select, Fill in the Blanks, True/False, Assertion-Reason, Match the Following
"""
from typing import Optional, Dict, Any, List
from backend.app.content.models import Question


def normalize_str(s: Optional[str]) -> str:
    if not s:
        return ""
    return s.strip().lower()


def evaluate_objective_response(
    question: Question,
    student_answer_json: Dict[str, Any],
    max_marks: float,
) -> tuple[Optional[float], bool]:
    """
    Evaluates student response against question answer data.
    Returns (score: Optional[float], is_auto_evaluated: bool)
    """
    q_type = question.type
    ans_data = question.answer_data or {}
    expected_answer = ans_data.get("expected_answer")
    answer_keys = ans_data.get("answer_keys", [])

    # 1. Single Choice MCQ / True False / Assertion Reason
    if q_type in ("mcq", "true_false", "assertion_reason"):
        student_choice = student_answer_json.get("selected_option") or student_answer_json.get("selected_key")
        if not student_choice:
            return 0.0, True

        target_expected = answer_keys[0] if answer_keys else expected_answer
        if normalize_str(student_choice) == normalize_str(target_expected):
            return float(max_marks), True
        return 0.0, True

    # 2. Multiple Select Questions
    elif q_type == "multiple_select":
        student_choices = student_answer_json.get("selected_options") or []
        if not student_choices:
            return 0.0, True

        clean_student = sorted([normalize_str(c) for c in student_choices])
        clean_keys = sorted([normalize_str(k) for k in answer_keys])

        if clean_student == clean_keys:
            return float(max_marks), True
        return 0.0, True

    # 3. Fill in the Blanks
    elif q_type == "fill_in_the_blanks":
        student_text = student_answer_json.get("text", "")
        if normalize_str(student_text) == normalize_str(expected_answer):
            return float(max_marks), True
        return 0.0, True

    # 4. Match the Following
    elif q_type == "match_the_following":
        student_pairs = student_answer_json.get("pairs") or {}
        # student_pairs example: {"1": "A", "2": "B"}
        # If expected is given as dict or string
        expected_pairs = ans_data.get("expected_pairs") or {}
        if expected_pairs and student_pairs == expected_pairs:
            return float(max_marks), True
        elif normalize_str(str(student_pairs)) == normalize_str(expected_answer):
            return float(max_marks), True
        return 0.0, True

    # 5. Subjective / Written / Numerical questions (require teacher evaluation)
    return None, False


class Tuple_Score:
    def __init__(self, score: Optional[float], is_auto: bool):
        self.score = score
        self.is_auto = is_auto
