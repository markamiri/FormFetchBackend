import sqlite3

def init_db():
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disclosure_links (
            id TEXT PRIMARY KEY,
            to TEXT NOT NULL,
            deadline TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_link(id, to, deadline):
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO disclosure_links (id, to, deadline) VALUES (?, ?, ?)", (id, to, deadline))
    conn.commit()
    conn.close()

def get_link(id):
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("SELECT to, deadline FROM disclosure_links WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    return {"to": result[0], "deadline": result[1]} if result else None
