"""
Mind V2 Database Seed Script
Seeds:
- 1 Platform Admin (platform.admin@mind.local)
- 2 Schools:
    1. Mind Demonstration Academy (slug: demo-school, code: MDA)
    2. St. Xavier's International School (slug: st-xaviers, code: SXI)
- Bands (Middle School 6–8, Secondary 9–10, Senior Secondary 11–12)
- Academic Year (2026-2027)
- 1 School Admin per school
- 3 Academic Coordinators (Middle, Secondary, Senior Secondary)
- 3 Teachers (with Maths teacher assigned to 11E, 12A, 12D, and Class Teacher flag)
- 3 Students (enrolled in 11E, 12A, 12D) with roll numbers
- 8 ICSE/ISC Subjects
- Classes & Sections
- Teacher Assignments
- ICSE / ISC Curriculum Nodes
- RoleAssignments for all users
"""
import asyncio
from datetime import date
from sqlalchemy import select
from backend.app.core.db import async_session_maker, engine, Base
from backend.app.core.security import hash_password
from backend.app.tenancy.models import School, AcademicYear, Band
from backend.app.identity.models import User, RoleAssignment, RoleName
from backend.app.academics.models import (
    Class,
    Section,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
    CurriculumNode,
)


async def seed():
    print("Beginning Mind V2 database seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # 1. Platform Admin (Global, no school)
        p_res = await session.execute(select(User).where(User.email == "platform.admin@mind.local"))
        platform_user = p_res.scalar_one_or_none()
        if not platform_user:
            platform_user = User(
                school_id=None,
                email="platform.admin@mind.local",
                password_hash=hash_password("PlatformPass123!"),
                full_name="Platform Administrator",
                designation="Global Systems Controller",
                status="active",
            )
            session.add(platform_user)
            await session.flush()

            ra_plat = RoleAssignment(
                user_id=platform_user.id,
                role=RoleName.PLATFORM_ADMIN,
                school_id=None,
                status="active"
            )
            session.add(ra_plat)
            await session.flush()
            print(f"Created Platform Admin: {platform_user.email}")

        # 2. Primary School: Mind Demonstration Academy
        res = await session.execute(select(School).where(School.slug == "demo-school"))
        school = res.scalar_one_or_none()
        if not school:
            school = School(
                name="Mind Demonstration Academy",
                slug="demo-school",
                code="MDA",
                board="ICSE/ISC",
                timezone="Asia/Kolkata",
                settings={"board": "ICSE/ISC", "pilot_mode": True, "feature_flags": {"online_exams": True, "ai_studio": True, "report_cards": True}},
            )
            session.add(school)
            await session.flush()
            print(f"Created School: {school.name} ({school.id})")

        # 2b. Secondary School: St. Xavier's International School
        res2 = await session.execute(select(School).where(School.slug == "st-xaviers"))
        school2 = res2.scalar_one_or_none()
        if not school2:
            school2 = School(
                name="St. Xavier's International School",
                slug="st-xaviers",
                code="SXI",
                board="ICSE/ISC",
                timezone="Asia/Kolkata",
                settings={"board": "ICSE/ISC", "pilot_mode": True},
            )
            session.add(school2)
            await session.flush()
            print(f"Created School 2: {school2.name} ({school2.id})")

        # 3. Bands for School 1
        bands_data = [
            ("Middle School (6-8)", 6, 8),
            ("Secondary (9-10)", 9, 10),
            ("Senior Secondary (11-12)", 11, 12),
        ]
        band_map = {}
        for b_name, min_g, max_g in bands_data:
            b_res = await session.execute(
                select(Band).where(Band.school_id == school.id, Band.name == b_name)
            )
            band = b_res.scalar_one_or_none()
            if not band:
                band = Band(school_id=school.id, name=b_name, min_grade=min_g, max_grade=max_g)
                session.add(band)
                await session.flush()
            band_map[b_name] = band

        # 4. Academic Year for School 1 & 2
        for s in (school, school2):
            res_year = await session.execute(
                select(AcademicYear).where(AcademicYear.school_id == s.id, AcademicYear.label == "2026-2027")
            )
            ay = res_year.scalar_one_or_none()
            if not ay:
                ay = AcademicYear(
                    school_id=s.id,
                    label="2026-2027",
                    starts_on=date(2026, 4, 1),
                    ends_on=date(2027, 3, 31),
                    status="active",
                )
                session.add(ay)
                await session.flush()

        res_year = await session.execute(
            select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.label == "2026-2027")
        )
        academic_year = res_year.scalar_one()

        # 5. Users for School 1
        users_to_seed = [
            # School Admin
            ("admin@mind.local", "AdminPass123!", "Dr. Alok Verma", RoleName.SCHOOL_ADMIN, "Principal / Academic Head", None),
            # Academic Coordinators for each band
            ("coord.senior@mind.local", "CoordPass123!", "Dr. Shweta Mukherjee", RoleName.ACADEMIC_COORDINATOR, "Senior Secondary Coordinator (11-12)", band_map["Senior Secondary (11-12)"].id),
            ("coord.secondary@mind.local", "CoordPass123!", "Sri Arvind Saxena", RoleName.ACADEMIC_COORDINATOR, "Secondary Coordinator (9-10)", band_map["Secondary (9-10)"].id),
            ("coord.middle@mind.local", "CoordPass123!", "Smt. Priya Nair", RoleName.ACADEMIC_COORDINATOR, "Middle School Coordinator (6-8)", band_map["Middle School (6-8)"].id),
            # Teachers
            ("maths.teacher@mind.local", "TeacherPass123!", "Smt. Sunita Rao", RoleName.TEACHER, "Senior PGT Mathematics", None),
            ("physics.teacher@mind.local", "TeacherPass123!", "Sri Rajesh Sharma", RoleName.TEACHER, "PGT Physics", None),
            ("cs.teacher@mind.local", "TeacherPass123!", "Mr. Vikram Mehta", RoleName.TEACHER, "PGT Computer Science", None),
            # Students
            ("student.aarav@mind.local", "StudentPass123!", "Aarav Gupta", RoleName.STUDENT, None, None),
            ("student.diya@mind.local", "StudentPass123!", "Diya Sen", RoleName.STUDENT, None, None),
            ("student.rohan@mind.local", "StudentPass123!", "Rohan Roy", RoleName.STUDENT, None, None),
        ]

        user_map = {}
        for email, pwd, name, role, desig, band_id in users_to_seed:
            u_res = await session.execute(select(User).where(User.school_id == school.id, User.email == email))
            u = u_res.scalar_one_or_none()
            if not u:
                u = User(
                    school_id=school.id,
                    email=email,
                    password_hash=hash_password(pwd),
                    full_name=name,
                    designation=desig,
                    status="active",
                    must_change_password=(role == RoleName.STUDENT),
                )
                session.add(u)
                await session.flush()

                ra = RoleAssignment(
                    user_id=u.id,
                    role=role,
                    school_id=school.id,
                    band_id=band_id,
                    status="active"
                )
                session.add(ra)
                await session.flush()
                print(f"Created User: {u.email} [{role}]")
            user_map[email] = u

        # School 2 Admin
        s2_admin_res = await session.execute(select(User).where(User.school_id == school2.id, User.email == "admin@stxaviers.local"))
        s2_admin = s2_admin_res.scalar_one_or_none()
        if not s2_admin:
            s2_admin = User(
                school_id=school2.id,
                email="admin@stxaviers.local",
                password_hash=hash_password("AdminPass123!"),
                full_name="Rev. Fr. Augustine",
                designation="Principal",
                status="active"
            )
            session.add(s2_admin)
            await session.flush()

            ra_s2 = RoleAssignment(user_id=s2_admin.id, role=RoleName.SCHOOL_ADMIN, school_id=school2.id, status="active")
            session.add(ra_s2)
            await session.flush()

        # 6. Subjects
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

        # 7. Classes & Sections
        class_map = {}
        section_map = {}

        class_configs = [
            ("Class 11", ["E", "A"], band_map["Senior Secondary (11-12)"].id, 11),
            ("Class 12", ["A", "D"], band_map["Senior Secondary (11-12)"].id, 12),
            ("Class 10", ["A"], band_map["Secondary (9-10)"].id, 10),
        ]

        for c_name, sec_names, band_id, grade_lvl in class_configs:
            c_res = await session.execute(
                select(Class).where(
                    Class.school_id == school.id,
                    Class.academic_year_id == academic_year.id,
                    Class.name == c_name,
                )
            )
            cls = c_res.scalar_one_or_none()
            if not cls:
                cls = Class(
                    school_id=school.id,
                    academic_year_id=academic_year.id,
                    band_id=band_id,
                    name=c_name,
                    grade_level=grade_lvl,
                )
                session.add(cls)
                await session.flush()
                print(f"Created Class: {cls.name}")
            class_map[c_name] = cls

            for s_name in sec_names:
                s_res = await session.execute(
                    select(Section).where(Section.class_id == cls.id, Section.name == s_name)
                )
                sec = s_res.scalar_one_or_none()
                if not sec:
                    sec = Section(class_id=cls.id, name=s_name)
                    session.add(sec)
                    await session.flush()
                    print(f"Created Section: {cls.name}-{sec.name}")
                section_map[f"{c_name}-{s_name}"] = sec

        # 8. Teacher Assignments
        # Maths Teacher -> 11E, 12A, 12D (Class Teacher of 11E)
        maths_teacher = user_map["maths.teacher@mind.local"]
        math_sub = subject_map["MATH"]

        maths_assignments = [
            ("Class 11", "E", True),   # Class Teacher of 11E!
            ("Class 12", "A", False),
            ("Class 12", "D", False),
        ]
        for c_n, s_n, is_ct in maths_assignments:
            cls = class_map[c_n]
            sec = section_map[f"{c_n}-{s_n}"]
            asgn_res = await session.execute(
                select(TeacherAssignment).where(
                    TeacherAssignment.school_id == school.id,
                    TeacherAssignment.teacher_id == maths_teacher.id,
                    TeacherAssignment.class_id == cls.id,
                    TeacherAssignment.section_id == sec.id,
                    TeacherAssignment.subject_id == math_sub.id,
                )
            )
            if not asgn_res.scalar_one_or_none():
                asgn = TeacherAssignment(
                    school_id=school.id,
                    teacher_id=maths_teacher.id,
                    class_id=cls.id,
                    section_id=sec.id,
                    subject_id=math_sub.id,
                    academic_year_id=academic_year.id,
                    is_class_teacher=is_ct,
                    status="active"
                )
                session.add(asgn)
                print(f"Assigned Maths Teacher to {c_n}-{s_n} (Class Teacher={is_ct})")

        # Physics Teacher -> 11E, 12A
        phys_teacher = user_map["physics.teacher@mind.local"]
        phy_sub = subject_map["PHY"]
        for c_n, s_n in [("Class 11", "E"), ("Class 12", "A")]:
            cls = class_map[c_n]
            sec = section_map[f"{c_n}-{s_n}"]
            asgn_res = await session.execute(
                select(TeacherAssignment).where(
                    TeacherAssignment.school_id == school.id,
                    TeacherAssignment.teacher_id == phys_teacher.id,
                    TeacherAssignment.class_id == cls.id,
                    TeacherAssignment.section_id == sec.id,
                    TeacherAssignment.subject_id == phy_sub.id,
                )
            )
            if not asgn_res.scalar_one_or_none():
                asgn = TeacherAssignment(
                    school_id=school.id,
                    teacher_id=phys_teacher.id,
                    class_id=cls.id,
                    section_id=sec.id,
                    subject_id=phy_sub.id,
                    academic_year_id=academic_year.id,
                    is_class_teacher=False,
                    status="active"
                )
                session.add(asgn)
                print(f"Assigned Physics Teacher to {c_n}-{s_n}")

        # 9. Student Enrollments with Roll Numbers
        student_assignments = [
            ("student.aarav@mind.local", "Class 11", "E", "11E-01"),
            ("student.diya@mind.local", "Class 12", "A", "12A-01"),
            ("student.rohan@mind.local", "Class 12", "D", "12D-01"),
        ]
        for s_email, c_n, s_n, roll_no in student_assignments:
            student = user_map[s_email]
            cls = class_map[c_n]
            sec = section_map[f"{c_n}-{s_n}"]
            enr_res = await session.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.school_id == school.id,
                    StudentEnrollment.student_id == student.id,
                )
            )
            if not enr_res.scalar_one_or_none():
                enr = StudentEnrollment(
                    school_id=school.id,
                    student_id=student.id,
                    class_id=cls.id,
                    section_id=sec.id,
                    academic_year_id=academic_year.id,
                    roll_number=roll_no,
                    status="active",
                )
                session.add(enr)
                print(f"Enrolled {student.full_name} in {c_n}-{s_n} (Roll: {roll_no})")

        # 10. ICSE/ISC Curriculum Nodes
        curriculum_samples = [
            ("PHY", "11", "Physical World & Measurement", "Units of measurement, systems of units, SI units"),
            ("PHY", "11", "Kinematics", "Motion in a straight line, Position-time graphical analysis"),
            ("PHY", "11", "Laws of Motion", "Newton's laws, impulse, conservation of linear momentum"),
            ("PHY", "12", "Electrostatics", "Electric charges, Coulomb's law, electric field & dipole"),
            ("PHY", "12", "Current Electricity", "Electric current, Ohm's law, Kirchhoff's rules"),
            ("MATH", "11", "Sets and Functions", "Sets and their representations, relations and functions"),
            ("MATH", "11", "Trigonometric Functions", "Trigonometric functions, identities and proofs"),
            ("MATH", "11", "Quadratic Equations", "Complex numbers, quadratic equations in complex number system"),
            ("MATH", "12", "Calculus - Derivatives", "Continuity and differentiability, chain rule, rates of change"),
            ("MATH", "12", "Calculus - Integrals", "Integration as inverse process of differentiation, definite integrals"),
            ("CS", "11", "Numbers & Boolean Algebra", "Propositional logic, truth tables, basic logic gates"),
            ("CS", "11", "Java Programming Fundamentals", "Primitive data types, operators, flow of control"),
            ("CS", "12", "Data Structures", "Arrays, Stacks, Queues, Binary Trees, Complexity analysis"),
        ]

        for s_code, grade, chapter, topic in curriculum_samples:
            sub = subject_map[s_code]
            c_res = await session.execute(
                select(CurriculumNode).where(
                    CurriculumNode.school_id == school.id,
                    CurriculumNode.subject_id == sub.id,
                    CurriculumNode.grade == grade,
                    CurriculumNode.chapter == chapter,
                    CurriculumNode.topic == topic,
                )
            )
            if not c_res.scalar_one_or_none():
                c_node = CurriculumNode(
                    school_id=school.id,
                    subject_id=sub.id,
                    grade=grade,
                    board="ICSE/ISC",
                    chapter=chapter,
                    topic=topic,
                    learning_outcome=f"Mastery of {topic} as prescribed in ICSE/ISC curriculum.",
                    source_ref=f"Council for the Indian School Certificate Examinations (CISCE) Syllabus - Class {grade}",
                )
                session.add(c_node)

        await session.commit()
        print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
