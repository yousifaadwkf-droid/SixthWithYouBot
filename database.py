import sqlite3

DB_NAME = "data.db"


def connect():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            student_id INTEGER PRIMARY KEY,
            answered INTEGER DEFAULT 0,
            answered_by TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            admin_message_id INTEGER PRIMARY KEY,
            admin_id INTEGER,
            student_id INTEGER
        )
    """)

    conn.commit()
    conn.close()


def save_student(user_id, username, first_name):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO students
        (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (user_id, username, first_name))

    conn.commit()
    conn.close()


def create_ticket(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO tickets
        (student_id, answered, answered_by)
        VALUES (?, 0, '')
    """, (student_id,))

    conn.commit()
    conn.close()


def save_message(admin_message_id, admin_id, student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO messages
        (admin_message_id, admin_id, student_id)
        VALUES (?, ?, ?)
    """, (
        admin_message_id,
        admin_id,
        student_id
    ))

    conn.commit()
    conn.close()


def get_student(message_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT student_id
        FROM messages
        WHERE admin_message_id = ?
    """, (message_id,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


def ticket_status(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT answered, answered_by
        FROM tickets
        WHERE student_id = ?
    """, (student_id,))

    row = cur.fetchone()

    conn.close()

    return row


def answer_ticket(student_id, admin_name):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tickets
        SET answered = 1,
            answered_by = ?
        WHERE student_id = ?
    """, (
        admin_name,
        student_id
    ))

    conn.commit()
    conn.close()


def get_admin_messages(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT admin_message_id, admin_id
        FROM messages
        WHERE student_id = ?
    """, (student_id,))

    rows = cur.fetchall()

    conn.close()

    return rows