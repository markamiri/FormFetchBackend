import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disclosure_links (
            id TEXT PRIMARY KEY,
            recipient TEXT NOT NULL,
            deadline TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_link(id, to, deadline):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO disclosure_links (id, recipient, deadline) VALUES (%s, %s, %s)",
        (id, to, deadline)
    )
    conn.commit()
    conn.close()

def get_link(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recipient, deadline FROM disclosure_links WHERE id = %s", (id,))
    result = cursor.fetchone()
    conn.close()
    return {"to": result[0], "deadline": result[1]} if result else None
