import csv
import io
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from fastapi.responses import Response

from backend.app.identity.models import User, UserRole
from backend.app.academics.models import Class, Section, Subject, StudentEnrollment
from backend.app.assessments.models import (
    Assessment,
    AssessmentItem,
    Attempt,
    AttemptStatus,
)
from backend.app.tenancy.models import School
from backend.app.analytics.service import AnalyticsService


class AssessmentExportService:
    @staticmethod
    async def export_results_csv(
        db: AsyncSession, user: User, assessment_id: str
    ) -> Response:
        """Export student gradebook roster and score breakdown as CSV."""
        stmt = (
            select(Assessment)
            .where(
                and_(
                    Assessment.id == assessment_id,
                    Assessment.school_id == user.school_id,
                )
            )
        )
        res = await db.execute(stmt)
        assessment = res.scalars().first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if not await AnalyticsService.verify_teacher_assessment_access(db, user, assessment):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to assessment results export.",
            )

        enrollments_stmt = (
            select(User.full_name, User.email, StudentEnrollment.roll_number, Attempt)
            .join(StudentEnrollment, User.id == StudentEnrollment.student_id)
            .join(Section, StudentEnrollment.section_id == Section.id)
            .outerjoin(
                Attempt,
                and_(
                    Attempt.student_id == User.id,
                    Attempt.assessment_id == assessment_id,
                ),
            )
            .where(
                and_(
                    User.school_id == user.school_id,
                    Section.class_id == assessment.class_id,
                )
            )
            .order_by(StudentEnrollment.roll_number.asc(), User.full_name.asc())
        )
        enr_res = await db.execute(enrollments_stmt)
        rows = enr_res.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Student Name",
            "Email",
            "Roll Number",
            "Attempt Status",
            "Total Score",
            "Max Marks",
            "Percentage",
            "Result Released",
            "Submitted At (UTC)",
        ])

        max_marks = float(assessment.total_marks or 1.0)

        for name, email, roll_no, attempt in rows:
            if attempt:
                att_status = attempt.status
                tot_score = attempt.total_score if attempt.total_score is not None else 0.0
                pct = round((tot_score / max_marks) * 100, 1) if max_marks > 0 else 0.0
                is_rel = "Yes" if attempt.is_released else "No"
                submitted_at = attempt.submitted_at.isoformat() if attempt.submitted_at else "N/A"
            else:
                att_status = "unattempted"
                tot_score = 0.0
                pct = 0.0
                is_rel = "No"
                submitted_at = "N/A"

            writer.writerow([
                name,
                email,
                roll_no or "",
                att_status,
                f"{tot_score:.1f}",
                f"{max_marks:.1f}",
                f"{pct:.1f}%",
                is_rel,
                submitted_at,
            ])

        csv_content = output.getvalue()
        filename = f"results_{assessment.title.replace(' ', '_').lower()}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    async def export_printable_paper(
        db: AsyncSession,
        user: User,
        assessment_id: str,
        include_marking_scheme: bool = False,
    ) -> Response:
        """Generates a clean, Board-exam-standard printable HTML view for the assessment."""
        stmt = (
            select(Assessment)
            .where(
                and_(
                    Assessment.id == assessment_id,
                    Assessment.school_id == user.school_id,
                )
            )
        )
        res = await db.execute(stmt)
        assessment = res.scalars().first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if user.role == UserRole.STUDENT and include_marking_scheme:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students cannot request marking schemes.",
            )

        school_stmt = select(School.name).where(School.id == user.school_id)
        school_res = await db.execute(school_stmt)
        school_name = school_res.scalar() or "Academic Institution"

        subj_stmt = select(Subject.name).where(Subject.id == assessment.subject_id)
        subj_res = await db.execute(subj_stmt)
        subject_name = subj_res.scalar() or "General Subject"

        class_stmt = select(Class.name).where(Class.id == assessment.class_id)
        class_res = await db.execute(class_stmt)
        class_name = class_res.scalar() or "Class"

        items_stmt = (
            select(AssessmentItem)
            .options(joinedload(AssessmentItem.question))
            .where(AssessmentItem.assessment_id == assessment_id)
            .order_by(AssessmentItem.position.asc())
        )
        items_res = await db.execute(items_stmt)
        items = list(items_res.scalars().all())

        html_parts = [
            """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>""" + assessment.title + """</title>
  <style>
    @page { margin: 20mm; size: A4; }
    body { font-family: 'Times New Roman', Times, serif; color: #111; line-height: 1.5; font-size: 11pt; margin: 20px; }
    .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }
    .school-title { font-size: 16pt; font-weight: bold; text-transform: uppercase; margin-bottom: 4px; }
    .exam-title { font-size: 14pt; font-weight: bold; margin-bottom: 4px; }
    .meta-row { display: flex; justify-content: space-between; font-weight: bold; margin-top: 8px; }
    .instructions { font-style: italic; font-size: 10pt; margin: 12px 0; border: 1px dashed #666; padding: 8px; }
    .question-block { margin-bottom: 16px; page-break-inside: avoid; }
    .question-header { display: flex; justify-content: space-between; font-weight: bold; }
    .prompt { margin-top: 4px; }
    .options { margin-left: 20px; margin-top: 6px; list-style-type: upper-alpha; }
    .options li { margin-bottom: 4px; }
    .marking-scheme { margin-top: 30px; border-top: 2px dashed #000; padding-top: 15px; page-break-before: always; }
    .scheme-item { background: #f9f9f9; border-left: 3px solid #2563eb; padding: 8px; margin-bottom: 10px; font-size: 10pt; }
    @media print {
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <div class="no-print" style="background:#e0e7ff; padding: 10px; margin-bottom: 20px; border-radius: 4px; text-align: right;">
    <button onclick="window.print()" style="padding: 8px 16px; font-weight: bold; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer;">Print / Save as PDF</button>
  </div>
  <div class="header">
    <div class="school-title">""" + school_name + """</div>
    <div class="exam-title">""" + assessment.title + """</div>
    <div class="meta-row">
      <span>Class: """ + class_name + """</span>
      <span>Subject: """ + subject_name + """</span>
      <span>Max Marks: """ + str(assessment.total_marks) + """</span>
    </div>
  </div>
  <div class="instructions">
    <strong>General Instructions:</strong>
    1. Answers to this paper must be written on the paper provided separately.<br>
    2. Attempt all questions. The intended marks for questions are given in brackets [ ].
  </div>
  <div class="questions">
"""
        ]

        for i, item in enumerate(items, 1):
            q = item.question
            marks = item.marks_override or (q.marks if q else 1)
            prompt = q.prompt if q else "Question prompt"
            html_parts.append(f"""
    <div class="question-block">
      <div class="question-header">
        <span>Question {i}</span>
        <span>[{marks} marks]</span>
      </div>
      <div class="prompt">{prompt}</div>
""")
            if q and q.content_data and isinstance(q.content_data.get("options"), list):
                html_parts.append('      <ol class="options">\n')
                for opt in q.content_data["options"]:
                    text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
                    html_parts.append(f'        <li>{text}</li>\n')
                html_parts.append('      </ol>\n')

            html_parts.append('    </div>\n')

        html_parts.append('  </div>\n')

        if include_marking_scheme:
            html_parts.append("""
  <div class="marking-scheme">
    <h2 style="text-align: center; text-transform: uppercase;">Confidential Teacher Marking Scheme & Key</h2>
""")
            for i, item in enumerate(items, 1):
                q = item.question
                correct = (
                    q.answer_data.get("correct_answer")
                    if q and q.answer_data
                    else "Subjective / Model Answer"
                )
                exp = (
                    q.answer_data.get("explanation")
                    if q and q.answer_data
                    else "Standard curriculum answer."
                )
                rubric = (
                    q.answer_data.get("rubric")
                    if q and q.answer_data
                    else "Full credit for conceptually sound derivation."
                )
                html_parts.append(f"""
    <div class="scheme-item">
      <strong>Q{i} Expected Answer:</strong> {correct}<br>
      <strong>Rationale / Explanation:</strong> {exp}<br>
      <strong>Rubric:</strong> {rubric}
    </div>
""")
            html_parts.append('  </div>\n')

        html_parts.append("""
</body>
</html>
""")
        full_html = "".join(html_parts)
        return Response(
            content=full_html,
            media_type="text/html",
            headers={"Content-Disposition": f'inline; filename="assessment_{assessment_id}.html"'},
        )
