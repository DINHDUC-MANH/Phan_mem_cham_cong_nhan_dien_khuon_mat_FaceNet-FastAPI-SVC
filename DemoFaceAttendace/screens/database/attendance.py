from database.connection import connect
from datetime import datetime

def save_attendance(label):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO attendance (label, timestamp) VALUES (?, ?)",
            (label, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

def get_attendances(limit=None):
    with connect() as conn:
        cur = conn.cursor()

        if limit:
            cur.execute("""
                SELECT id, label, timestamp
                FROM attendance
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        else:
            cur.execute("""
                SELECT id, label, timestamp
                FROM attendance
                ORDER BY timestamp DESC
            """)

        return cur.fetchall()