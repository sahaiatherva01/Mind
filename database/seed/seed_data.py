"""
Mind V1 Database Seed Script
Seeds:
- Demo School
- Academic Year (2026-2027)
- 1 Admin
- 3 Teachers (including Maths teacher assigned to 11E, 12A, 12D)
- 3 Students (enrolled in 11E, 12A, 12D)
- 8 ICSE/ISC Subjects (Physics, Chemistry, Maths, Biology, History, Geography, English, Computer Science)
- Classes & Sections (Class 11E, 12A, 12D, 10A)
- Teacher Assignments
- ICSE / ISC Curriculum Nodes
"""
import asyncio
from datetime import date
from sqlalchemy import select
from backend.app.core.db import async_session_maker, engine, Base
from backend.app.core.security import hash_password
from backend.app.tenancy.models import School, AcademicYear
from backend.app.identity.models import User
from backend.app.academics.models import (
    Class,
    Section,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
    CurriculumNode,
)


async def seed():
    print("Beginning database seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # 1. School
        res = await session.execute(select(School).where(School.slug == "demo-school"))
        school = res.scalar_one_or_none()
        if not school:
            school = School(
                name="Mind Demonstration Academy",
                slug="demo-school",
                timezone="Asia/Kolkata",
                settings={"board": "ICSE/ISC", "pilot_mode": True},
            )
            session.add(school)
            await session.flush()
            print(f"Created School: {school.name} ({school.id})")

        # 2. Academic Year
        res_year = await session.execute(
            select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.label == "2026-2027")
        )
        academic_year = res_year.scalar_one_or_none()
        if not academic_year:
            academic_year = AcademicYear(
                school_id=school.id,
                label="2026-2027",
                starts_on=date(2026, 4, 1),
                ends_on=date(2027, 3, 31),
                status="active",
            )
            session.add(academic_year)
            await session.flush()
            print(f"Created Academic Year: {academic_year.label}")

        # 3. Users
        users_to_seed = [
            ("admin@mind.local", "AdminPass123!", "Dr. Alok Verma", "admin", "Principal / Academic Head"),
            ("maths.teacher@mind.local", "TeacherPass123!", "Smt. Sunita Rao", "teacher", "Senior PGT Mathematics"),
            ("physics.teacher@mind.local", "TeacherPass123!", "Sri Rajesh Sharma", "teacher", "PGT Physics"),
            ("cs.teacher@mind.local", "TeacherPass123!", "Mr. Vikram Mehta", "teacher", "PGT Computer Science"),
            ("student.aarav@mind.local", "StudentPass123!", "Aarav Gupta", "student", None),
            ("student.diya@mind.local", "StudentPass123!", "Diya Sen", "student", None),
            ("student.rohan@mind.local", "StudentPass123!", "Rohan Roy", "student", None),
        ]

        user_map = {}
        for email, pwd, name, role, desig in users_to_seed:
            u_res = await session.execute(select(User).where(User.school_id == school.id, User.email == email))
            u = u_res.scalar_one_or_none()
            if not u:
                u = User(
                    school_id=school.id,
                    email=email,
                    password_hash=hash_password(pwd),
                    full_name=name,
                    role=role,
                    designation=desig,
                    status="active",
                )
                session.add(u)
                await session.flush()
                print(f"Created User: {u.email} [{u.role}]")
            user_map[email] = u

        # 4. Subjects
        subjects_data = [
            ("Physics", "PHY"),
            ("Chemistry", "CHEM"),
            ("Mathematics", "MATH"),
            ("Biology", "BIO"),
            ("History", "HIST"),
            ("Geography", "GEOG"),
            ("English", "ENG"),
            ("Computer Science", "CS"),
        ]
        subject_map = {}
        for s_name, s_code in subjects_data:
            s_res = await session.execute(
                select(Subject).where(Subject.school_id == school.id, Subject.code == s_code)
            )
            sub = s_res.scalar_one_or_none()
            if not sub:
                sub = Subject(school_id=school.id, name=s_name, code=s_code)
                session.add(sub)
                await session.flush()
                print(f"Created Subject: {sub.name} ({sub.code})")
            subject_map[s_code] = sub

        # 5. Classes & Sections (Class 11, Class 12, Class 10)
        class_map = {}
        section_map = {}

        class_configs = [
            ("Class 11", ["E", "A"]),
            ("Class 12", ["A", "D"]),
            ("Class 10", ["A"]),
        ]

        for c_name, sec_names in class_configs:
            c_res = await session.execute(
                select(Class).where(
                    Class.school_id == school.id,
                    Class.academic_year_id == academic_year.id,
                    Class.name == c_name
                )
            )
            c = c_res.scalar_one_or_none()
            if not c:
                c = Class(school_id=school.id, academic_year_id=academic_year.id, name=c_name)
                session.add(c)
                await session.flush()
                print(f"Created Class: {c.name}")
            class_map[c_name] = c

            for s_name in sec_names:
                sec_key = f"{c_name}-{s_name}"
                s_res = await session.execute(
                    select(Section).where(Section.class_id == c.id, Section.name == s_name)
                )
                sec = s_res.scalar_one_or_none()
                if not sec:
                    sec = Section(class_id=c.id, name=s_name)
                    session.add(sec)
                    await session.flush()
                    print(f"  Created Section: {sec_key}")
                section_map[sec_key] = sec

        # 6. Teacher Assignments
        # Maths teacher assigned to 11E, 12A, 12D (per docs specification)
        assignments_to_create = [
            ("maths.teacher@mind.local", "Class 11", "E", "MATH"),
            ("maths.teacher@mind.local", "Class 12", "A", "MATH"),
            ("maths.teacher@mind.local", "Class 12", "D", "MATH"),
            ("physics.teacher@mind.local", "Class 11", "E", "PHY"),
            ("physics.teacher@mind.local", "Class 12", "A", "PHY"),
            ("cs.teacher@mind.local", "Class 12", "D", "CS"),
        ]

        for t_email, c_name, s_name, sub_code in assignments_to_create:
            t_user = user_map[t_email]
            cls_obj = class_map[c_name]
            sec_obj = section_map[f"{c_name}-{s_name}"]
            sub_obj = subject_map[sub_code]

            asgn_res = await session.execute(
                select(TeacherAssignment).where(
                    TeacherAssignment.school_id == school.id,
                    TeacherAssignment.teacher_id == t_user.id,
                    TeacherAssignment.class_id == cls_obj.id,
                    TeacherAssignment.section_id == sec_obj.id,
                    TeacherAssignment.subject_id == sub_obj.id,
                )
            )
            if not asgn_res.scalar_one_or_none():
                asgn = TeacherAssignment(
                    school_id=school.id,
                    teacher_id=t_user.id,
                    class_id=cls_obj.id,
                    section_id=sec_obj.id,
                    subject_id=sub_obj.id,
                )
                session.add(asgn)
                await session.flush()
                print(f"Assigned {t_email} -> {c_name} {s_name} [{sub_code}]")

        # 7. Student Enrollments
        enrollments_to_create = [
            ("student.aarav@mind.local", "Class 11", "E", "11E-01"),
            ("student.diya@mind.local", "Class 12", "A", "12A-04"),
            ("student.rohan@mind.local", "Class 12", "D", "12D-12"),
        ]

        for s_email, c_name, s_name, roll in enrollments_to_create:
            s_user = user_map[s_email]
            cls_obj = class_map[c_name]
            sec_obj = section_map[f"{c_name}-{s_name}"]

            enr_res = await session.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.school_id == school.id,
                    StudentEnrollment.student_id == s_user.id,
                    StudentEnrollment.class_id == cls_obj.id,
                    StudentEnrollment.section_id == sec_obj.id,
                )
            )
            if not enr_res.scalar_one_or_none():
                enr = StudentEnrollment(
                    school_id=school.id,
                    student_id=s_user.id,
                    class_id=cls_obj.id,
                    section_id=sec_obj.id,
                    roll_number=roll,
                    status="active",
                )
                session.add(enr)
                await session.flush()
                print(f"Enrolled {s_email} -> {c_name} {s_name} (Roll: {roll})")

        # 8. Sample Curriculum Nodes (ICSE/ISC)
        curriculum_samples = [
            ("MATH", "11", "Quadratic Equations", "Nature of Roots", "Determine real and complex roots of quadratic equations"),
            ("MATH", "11", "Quadratic Equations", "Factorisation & Quadratic Formula", "Apply discriminant method to solve polynomials"),
            ("MATH", "12", "Calculus", "Derivatives and Tangents", "Calculate first and second order derivatives"),
            ("PHY", "11", "Kinematics", "Motion in One Dimension", "Apply equations of motion to uniformly accelerated systems"),
            ("PHY", "12", "Electromagnetism", "Coulomb's Law & Electric Fields", "Calculate electric field vectors for point charges"),
            ("CS", "12", "Data Structures", "Binary Search Trees", "Implement traversal, insertion, and deletion algorithms in Java"),
            ("BIO", "12", "Genetics & Evolution", "Mendelian Inheritance", "Analyze monohybrid and dihybrid cross ratios"),
            ("CHEM", "11", "Chemical Bonding", "Hybridization & VSEPR", "Predict molecular geometries and bond angles"),
        ]

        for sub_code, grade, chapter, topic, outcome in curriculum_samples:
            sub_obj = subject_map[sub_code]
            c_node_res = await session.execute(
                select(CurriculumNode).where(
                    CurriculumNode.school_id == school.id,
                    CurriculumNode.subject_id == sub_obj.id,
                    CurriculumNode.chapter == chapter,
                    CurriculumNode.topic == topic,
                )
            )
            if not c_node_res.scalar_one_or_none():
                node = CurriculumNode(
                    school_id=school.id,
                    subject_id=sub_obj.id,
                    grade=grade,
                    board="ICSE/ISC",
                    chapter=chapter,
                    topic=topic,
                    learning_outcome=outcome,
                    source_ref="ICSE/ISC Prescribed Syllabus 2026-27",
                )
                session.add(node)
                await session.flush()
                print(f"Curriculum Seeded: [{sub_code}] Class {grade} - {chapter} > {topic}")

        await session.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())

