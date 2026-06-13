from __future__ import annotations

from app.data import COURSES, EXAMS, PROFILE


class AcademicsServer:
    source = "academic_section"

    def summary(self) -> dict:
        average_attendance = round(sum(course["attendance"] for course in COURSES) / len(COURSES))
        return {
            "profile": PROFILE,
            "cgpa": PROFILE["cgpa"],
            "average_attendance": average_attendance,
            "courses": COURSES,
            "exams": EXAMS,
        }

    def low_attendance(self, threshold: int = 75) -> list[dict]:
        return [course for course in COURSES if course["attendance"] < threshold]


academics_server = AcademicsServer()
