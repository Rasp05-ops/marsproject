from __future__ import annotations

from datetime import date


LIBRARY_BOOKS = [
    {"id": "book-001", "title": "Introduction to Algorithms", "author": "CLRS", "status": "available", "due": None},
    {"id": "book-002", "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "status": "borrowed", "due": "2026-06-18"},
    {"id": "book-003", "title": "Designing Data-Intensive Apps", "author": "Martin Kleppmann", "status": "available", "due": None},
    {"id": "book-004", "title": "Clean Code", "author": "Robert Martin", "status": "reserved", "due": "2026-06-15"},
    {"id": "book-005", "title": "Deep Learning", "author": "Goodfellow et al.", "status": "available", "due": None},
    {"id": "book-006", "title": "Operating System Concepts", "author": "Silberschatz", "status": "borrowed", "due": "2026-06-20"},
]

MENU = {
    "breakfast": ["Poha + Chai", "Idli Sambar", "Bread Butter Jam", "Banana"],
    "lunch": ["Dal Makhani", "Rajma Chawal", "Roti + Sabzi", "Salad + Curd"],
    "snacks": ["Samosa", "Chai / Coffee", "Biscuits"],
    "dinner": ["Paneer Butter Masala", "Jeera Rice", "Chapati", "Kheer"],
}

CAFETERIA_TIMINGS = {
    "breakfast": "7:30 AM - 9:30 AM",
    "lunch": "12:30 PM - 2:30 PM",
    "snacks": "4:30 PM - 6:00 PM",
    "dinner": "7:30 PM - 9:30 PM",
}

EVENTS = [
    {"id": "event-001", "name": "ML Workshop: LangGraph Hands-on", "org": "SDSLabs", "date": "2026-06-14", "time": "3:00 PM", "venue": "LHC 101", "tag": "Tech"},
    {"id": "event-002", "name": "Robotics Club Open Session", "org": "Robocon", "date": "2026-06-15", "time": "5:00 PM", "venue": "Electronics Lab", "tag": "Tech"},
    {"id": "event-003", "name": "Cognizance Final Ceremony", "org": "Technical Council", "date": "2026-06-16", "time": "6:00 PM", "venue": "Convocation Hall", "tag": "Fest"},
    {"id": "event-004", "name": "Hindi Debate Competition", "org": "Cultural Council", "date": "2026-06-17", "time": "4:00 PM", "venue": "SAC Auditorium", "tag": "Cultural"},
    {"id": "event-005", "name": "Entrepreneurship Summit", "org": "E-Cell", "date": "2026-06-19", "time": "10:00 AM", "venue": "IIC Hall", "tag": "Career"},
    {"id": "event-006", "name": "Photography Walk: Campus", "org": "PhotoClub", "date": "2026-06-21", "time": "6:30 AM", "venue": "Main Gate", "tag": "Cultural"},
]

NOTICES = [
    {"id": "notice-001", "title": "End-Sem Examination Schedule Released", "from": "Academic Section", "date": "2026-06-12", "urgent": True},
    {"id": "notice-002", "title": "Last Date for Fee Payment: June 20", "from": "Accounts Section", "date": "2026-06-11", "urgent": True},
    {"id": "notice-003", "title": "Library Returns Due Before Exams", "from": "Central Library", "date": "2026-06-10", "urgent": False},
    {"id": "notice-004", "title": "Hostel Allotment for New Students", "from": "Hostel Office", "date": "2026-06-09", "urgent": False},
    {"id": "notice-005", "title": "Scholarship Form Submission Open", "from": "Welfare Section", "date": "2026-06-08", "urgent": False},
]

COURSES = [
    {"code": "CS-301", "name": "Algorithms", "prof": "Dr. Mehta", "attendance": 82, "grade": "A"},
    {"code": "CS-305", "name": "Operating Systems", "prof": "Dr. Singh", "attendance": 76, "grade": "B+"},
    {"code": "CS-309", "name": "Machine Learning", "prof": "Dr. Rao", "attendance": 91, "grade": "A+"},
    {"code": "MA-201", "name": "Probability & Stats", "prof": "Dr. Sharma", "attendance": 68, "grade": "B"},
    {"code": "HSS-203", "name": "Economics", "prof": "Dr. Verma", "attendance": 88, "grade": "A"},
]

EXAMS = [
    {"course_code": "CS-301", "course": "Algorithms", "date": "2026-06-24", "time": "9:00 AM"},
    {"course_code": "MA-201", "course": "Probability & Stats", "date": "2026-06-25", "time": "9:00 AM"},
    {"course_code": "CS-309", "course": "Machine Learning", "date": "2026-06-27", "time": "2:00 PM"},
]

PROFILE = {
    "name": "Anirudh",
    "institute": "IIT Roorkee",
    "program": "B.Tech CSE",
    "semester": "5th Sem",
    "today": date(2026, 6, 13).isoformat(),
    "cgpa": 8.7,
}
