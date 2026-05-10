import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
    name TEXT,
    username TEXT,
    invites INTEGER DEFAULT 0,
    invited_by INTEGER
)
''')

conn.commit()


def add_user(user_id, name, username, invited_by=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, name, username, invited_by) VALUES (?, ?, ?, ?)",
            (user_id, name, username, invited_by)
        )

        if invited_by:
            cursor.execute(
                "UPDATE users SET invites = invites + 1 WHERE user_id=?",
                (invited_by,)
            )

        conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()