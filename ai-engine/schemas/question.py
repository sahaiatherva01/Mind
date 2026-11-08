"""
Canonical Question Schema supporting 40 ICSE/ISC Board Exam Question Types
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# 40 Question Types across 5 Categories
QuestionCategory = Literal[
    "objective",
    "written",
    "visual_mathematical",
    "application_analytical",
    "computer_science"
]

QuestionType = Literal[
    # Objective questions (6)
    "mcq",
    "multiple_select",
    "fill_in_the_blanks",
    "true_false",
    "match_the_following",
    "assertion_reason",

    # Written questions (8)
    "very_short_answer",
    "short_answer",
    "medium_answer",
    "long_answer",
    "definition_based",
    "difference_based",
    "reasoning_based",
    "proof_derivation_based",

    # Visual and mathematical questions (9)
    "diagram_based",
    "label_the_diagram",
    "graph_based",
    "table_based",
    "chart_based",
    "map_based",
    "construction_based",
    "numerical_based",
    "formula_based",

    # Application and analytical questions (9)
    "case_based",
    "passage_based",
    "source_based",
    "data_interpretation",
    "application_based",
    "hots",
    "critical_thinking",
    "problem_solving",
    "experiment_based",

    # Computer Science questions (8)
    "output_prediction",
    "theory_coding",
    "code_completion",
    "error_detection",
    "debugging",
    "dry_run",
    "algorithm_writing",
    "program_writing",
    "data_structure_implementation",
]

DifficultyLevel = Literal["easy", "medium", "hard"]
QuestionStatus = Literal["draft", "approved", "archived"]


class MatchPair(BaseModel):
    left: str
    right: str


class QuestionOption(BaseModel):
    id: str  # e.g., "A", "B", "C", "D"
    text: str


class CanonicalQuestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: QuestionCategory
    type: QuestionType
    prompt: str
    marks: int = Field(..., ge=1, le=100)
    difficulty: DifficultyLevel = "medium"
    topic_tags: List[str] = []

    # Objective choices / context
    options: Optional[List[QuestionOption]] = None
    match_pairs: Optional[List[MatchPair]] = None
    passage_or_case_text: Optional[str] = None
    code_snippet: Optional[str] = None
    diagram_description: Optional[str] = None

    # Expected answer & explanation (Teacher-only until release)
    expected_answer: str
    answer_keys: Optional[List[str]] = None  # e.g., ["A"] or ["A", "C"] for multiple select
    marking_scheme: Optional[str] = None
    rationale: Optional[str] = None

    # Quality flags & metadata
    flagged_uncertain: bool = False
    status: QuestionStatus = "draft"
    version: int = 1


class GenerationRequestSpec(BaseModel):
    output_type: Literal["worksheet", "quiz", "question_paper", "custom_question_set"]
    subject_id: str
    class_id: str
    section_id: str
    chapter: str
    topics: List[str]
    question_types: List[QuestionType]
    question_count: int = Field(..., ge=1, le=50)
    total_marks: int = Field(..., ge=1, le=100)
    difficulty_distribution: Dict[DifficultyLevel, int] = {"easy": 30, "medium": 50, "hard": 20}
    instructions: Optional[str] = None
    board: str = "ICSE/ISC"
    language: str = "en"
