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
            handled_by_id INTEGER,
            handled_by_name TEXT
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


def save_message(admin_msg_id, admin_id, student_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO messages VALUES (?, ?, ?)", (int(admin_msg_id), int(admin_id), int(student_id)))
    conn.commit()
    conn.close()


def get_student(admin_msg_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT student_id FROM messages WHERE message_id = ?", (int(admin_msg_id),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def create_ticket(student_id):
    """إعادة فتح التذكرة وإلغاء حجز المشرف السابق عند وصول رسالة جديدة من الطالب"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tickets (student_id, status, handled_by_id, handled_by_name)
        VALUES (?, 'open', NULL, NULL)
        ON CONFLICT(student_id) DO UPDATE SET
        status = 'open',
        handled_by_id = NULL,
        handled_by_name = NULL
    """, (int(student_id),))
    conn.commit()
    conn.close()


def get_ticket(student_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT status, handled_by_id, handled_by_name FROM tickets WHERE student_id = ?", (int(student_id),))
    row = cur.fetchone()
    conn.close()
    return row


def assign_and_answer_ticket(student_id, admin_id, admin_name):
    """حجز التذكرة للمشرف وإبقاء حظر بقية المشرفين"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        UPDATE tickets 
        SET status = 'answered', handled_by_id = ?, handled_by_name = ?
        WHERE student_id = ?
    """, (int(admin_id), str(admin_name), int(student_id)))
    conn.commit()
    conn.close()