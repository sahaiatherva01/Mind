"""
Deterministic Mock AI Provider
Generates authentic ICSE/ISC questions across all 40 question types offline without API keys or costs.
"""
import uuid
from typing import List
from ai_engine.adapters.base import BaseAIProvider
from ai_engine.schemas.question import (
    CanonicalQuestion,
    GenerationRequestSpec,
    QuestionOption,
    MatchPair,
    QuestionCategory,
    QuestionType,
)


def get_category_for_type(qtype: QuestionType) -> QuestionCategory:
    if qtype in ("mcq", "multiple_select", "fill_in_the_blanks", "true_false", "match_the_following", "assertion_reason"):
        return "objective"
    elif qtype in ("very_short_answer", "short_answer", "medium_answer", "long_answer", "definition_based", "difference_based", "reasoning_based", "proof_derivation_based"):
        return "written"
    elif qtype in ("diagram_based", "label_the_diagram", "graph_based", "table_based", "chart_based", "map_based", "construction_based", "numerical_based", "formula_based"):
        return "visual_mathematical"
    elif qtype in ("case_based", "passage_based", "source_based", "data_interpretation", "application_based", "hots", "critical_thinking", "problem_solving", "experiment_based"):
        return "application_analytical"
    elif qtype in ("output_prediction", "theory_coding", "code_completion", "error_detection", "debugging", "dry_run", "algorithm_writing", "program_writing", "data_structure_implementation"):
        return "computer_science"
    return "written"


class MockAIProvider(BaseAIProvider):
    async def generate_questions(
        self,
        spec: GenerationRequestSpec,
        prompt_template: str,
    ) -> List[CanonicalQuestion]:
        questions: List[CanonicalQuestion] = []
        target_count = spec.question_count
        marks_per_q = max(1, spec.total_marks // target_count)
        types_to_cycle = spec.question_types if spec.question_types else ["mcq", "short_answer", "numerical_based"]

        for idx in range(target_count):
            q_id = str(uuid.uuid4())
            q_type = types_to_cycle[idx % len(types_to_cycle)]
            category = get_category_for_type(q_type)
            topic = spec.topics[idx % len(spec.topics)] if spec.topics else spec.chapter

            # Build questions tailored to category and ICSE/ISC context
            if q_type == "mcq":
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt=f"In {spec.chapter} ({topic}), what is the primary condition for real and distinct roots of ax² + bx + c = 0?",
                    marks=marks_per_q,
                    difficulty="easy",
                    topic_tags=[topic, spec.chapter],
                    options=[
                        QuestionOption(id="A", text="Discriminant b² - 4ac > 0"),
                        QuestionOption(id="B", text="Discriminant b² - 4ac = 0"),
                        QuestionOption(id="C", text="Discriminant b² - 4ac < 0"),
                        QuestionOption(id="D", text="b² + 4ac = 0"),
                    ],
                    expected_answer="A",
                    answer_keys=["A"],
                    rationale="For real and distinct roots, the discriminant D = b² - 4ac must be strictly positive.",
                )
            elif q_type == "assertion_reason":
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt="Assertion (A): Electric field lines never intersect each other.\nReason (R): At the point of intersection, there would be two directions of electric field, which is impossible.",
                    marks=marks_per_q,
                    difficulty="medium",
                    topic_tags=[topic, "Electromagnetism"],
                    options=[
                        QuestionOption(id="A", text="Both A and R are true and R is the correct explanation of A"),
                        QuestionOption(id="B", text="Both A and R are true but R is NOT the correct explanation of A"),
                        QuestionOption(id="C", text="A is true but R is false"),
                        QuestionOption(id="D", text="A is false but R is true"),
                    ],
                    expected_answer="A",
                    answer_keys=["A"],
                    rationale="If two electric field lines intersected, a unit test charge at that point would experience two different directions of resultant electrostatic force simultaneously.",
                )
            elif q_type == "match_the_following":
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt="Match the following physical quantities with their SI dimensions:",
                    marks=marks_per_q,
                    difficulty="medium",
                    topic_tags=[topic],
                    match_pairs=[
                        MatchPair(left="Electric Potential", right="[M L² T⁻³ A⁻¹]"),
                        MatchPair(left="Capacitance", right="[M⁻¹ L⁻² T⁴ A²]"),
                        MatchPair(left="Magnetic Flux", right="[M L² T⁻² A⁻¹]"),
                    ],
                    expected_answer="1-A, 2-B, 3-C",
                    rationale="Derived directly from standard dimensional analysis in ISC Physics.",
                )
            elif q_type in ("output_prediction", "dry_run", "debugging"):
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt="Predict the output of the following Java snippet for Class 12 ISC Computer Science:",
                    marks=marks_per_q,
                    difficulty="medium",
                    topic_tags=[topic, "Java"],
                    code_snippet="int a = 5, b = 2;\nSystem.out.println(a++ * ++b + a / b);",
                    expected_answer="Output: 17",
                    marking_scheme="1 mark for sub-expression values (a++ = 5, ++b = 3), 1 mark for integer division (6 / 3 = 2), 1 mark for final result 17.",
                    rationale="a++ evaluates to 5 (a becomes 6). ++b evaluates to 3 (b becomes 3). 5 * 3 = 15. Then a / b = 6 / 3 = 2. 15 + 2 = 17.",
                )
            elif q_type == "numerical_based":
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt=f"A projectile is fired with an initial velocity of 40 m/s at an angle of 30° above the horizontal. Calculate the maximum height attained (Take g = 10 m/s²).",
                    marks=marks_per_q,
                    difficulty="medium",
                    topic_tags=[topic, "Kinematics"],
                    expected_answer="Maximum Height H = 20 metres",
                    marking_scheme="1 mark for formula H = (u² sin²θ)/(2g), 1 mark for substitution, 1 mark for final value with SI units.",
                    rationale="H = (40² * sin²(30°)) / (2 * 10) = (1600 * 0.25) / 20 = 400 / 20 = 20 m.",
                )
            elif q_type == "proof_derivation_based":
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt="Derive the expression for the electric field due to an electric dipole at an axial point using Coulomb's law.",
                    marks=marks_per_q,
                    difficulty="hard",
                    topic_tags=[topic, "Derivation"],
                    expected_answer="E_axial = (1 / 4πε₀) * (2pr / (r² - a²)²)",
                    marking_scheme="1 mark for diagram, 2 marks for vector superposition of E+ and E-, 1 mark for algebraic simplification, 1 mark for short dipole approximation E = 2kp/r³.",
                    rationale="Standard ISC Class 12 electrostatics derivation.",
                )
            else:
                # Default written / analytical question
                q = CanonicalQuestion(
                    id=q_id,
                    category=category,
                    type=q_type,
                    prompt=f"Explain the conceptual difference between {topic} and related phenomena in {spec.chapter}. Provide two distinguishing points.",
                    marks=marks_per_q,
                    difficulty="medium",
                    topic_tags=[topic],
                    expected_answer=f"Point 1: Fundamental definition in {topic}. Point 2: Operational behavior under board conditions.",
                    marking_scheme="1 mark for each distinct, factually correct point.",
                    rationale=f"Addresses key learning outcomes prescribed in the ICSE/ISC syllabus for {spec.chapter}.",
                )

            questions.append(q)

        # Adjust total marks to match spec.total_marks exactly
        allocated = sum(q.marks for q in questions)
        diff = spec.total_marks - allocated
        if diff != 0 and questions:
            questions[0].marks += diff

        return questions

    async def regenerate_single_question(
        self,
        existing_question: CanonicalQuestion,
        feedback: str,
    ) -> CanonicalQuestion:
        # Clone with updated prompt and ID
        new_q = existing_question.model_copy(deep=True)
        new_q.id = str(uuid.uuid4())
        new_q.prompt = f"{existing_question.prompt} [Revised: {feedback}]"
        new_q.version += 1
        return new_q

