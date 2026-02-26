from database.connection import connect

def save_user(label):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO user (label) VALUES (?)",
            (label,)
        )

def get_users():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, label FROM user ORDER BY label")
        return cur.fetchall()