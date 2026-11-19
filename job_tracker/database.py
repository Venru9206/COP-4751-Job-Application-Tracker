# database.py
import os
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD", ""),
        database="job_tracker",
    )

def calculate_match(user_skills, required_skills):
    user_set = {s.strip().lower() for s in user_skills}
    required = [s.strip() for s in required_skills if s.strip()]
    if not required:
        return None, []
    missing = [s for s in required if s.lower() not in user_set]
    matched = len(required) - len(missing)
    percent = round(matched / len(required) * 100, 1)
    return percent, missing
