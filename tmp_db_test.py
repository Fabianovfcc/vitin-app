import sqlite3
import os

db_path = 'backend/data/vitin.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    # Insert
    conn.execute("INSERT INTO students (name) VALUES ('TEST_SAVE_SYSTEM')")
    conn.commit()
    
    # Verify
    res = conn.execute("SELECT name FROM students WHERE name = 'TEST_SAVE_SYSTEM'").fetchone()
    if res:
        print("SAVE_VERIFIED_SUCCESS")
        # Cleanup
        conn.execute("DELETE FROM students WHERE name = 'TEST_SAVE_SYSTEM'")
        conn.commit()
    else:
        print("SAVE_FAILED_NO_RECORD")
    conn.close()
except Exception as e:
    print(f"DATABASE_ERROR: {e}")
