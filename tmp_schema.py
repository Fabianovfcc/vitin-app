import sqlite3
import json

def get_schema():
    conn = sqlite3.connect('backend/data/vitin.db')
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    schema = {}
    for table_name in [t[0] for t in tables]:
        columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        schema[table_name] = [c[1] for c in columns]
    conn.close()
    return schema

if __name__ == "__main__":
    print(json.dumps(get_schema(), indent=2))
