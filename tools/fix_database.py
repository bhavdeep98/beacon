"""Fix database schema"""
import sqlite3

conn = sqlite3.connect('psyflo.db')
cursor = conn.cursor()

try:
    # Add student_id_hash column to crisis_events if it doesn't exist
    cursor.execute("ALTER TABLE crisis_events ADD COLUMN student_id_hash VARCHAR(64);")
    print("✅ Added student_id_hash column to crisis_events")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✅ Column already exists")
    else:
        print(f"❌ Error: {e}")

conn.commit()
conn.close()
print("✅ Database fixed")
