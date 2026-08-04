import sqlite3

DB_NAME = "bot_database.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY,
            admin_id INTEGER,
            student_id INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            student_id INTEGER PRIMARY KEY,
            status TEXT,
            handled_by TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def save_student(user_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO students VALUES (?, ?, ?)", (int(user_id), str(username or ''), str(first_name or '')))
    conn.commit()
    conn.close()


def save_message(message_id, admin_id, student_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO messages VALUES (?, ?, ?)", (int(message_id), int(admin_id), int(student_id)))
    conn.commit()
    conn.close()


def get_student(message_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT student_id FROM messages WHERE message_id = ?", (int(message_id),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def create_ticket(student_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # إعادة فتح تذكرة جديدة عند وصول سؤال جديد من الطالب
    cur.execute("INSERT OR REPLACE INTO tickets (student_id, status, handled_by) VALUES (?, 'open', NULL)", (int(student_id),))
    conn.commit()
    conn.close()


def get_ticket(student_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT status, handled_by FROM tickets WHERE student_id = ?", (int(student_id),))
    row = cur.fetchone()
    conn.close()
    return row


def answer_ticket(student_id, admin_info):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # إغلاق التذكرة وتسجيل المشرف الذي قام بالرد
    cur.execute("INSERT OR REPLACE INTO tickets (student_id, status, handled_by) VALUES (?, 'answered', ?)", (int(student_id), str(admin_info)))
    conn.commit()
    conn.close()