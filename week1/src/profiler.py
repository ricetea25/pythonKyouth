import sqlite3
import os

def run_data_profile(db_path):
    # Prevent crash if DB doesn't exist
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Total Records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_records = cursor.fetchone()[0]

        # Null Values
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN job_title IS NULL OR job_title = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END)
            FROM jobs
        """)
        nulls = cursor.fetchone()

        # Avg Length
        cursor.execute("SELECT AVG(LENGTH(description)) FROM jobs")
        avg_len = int(cursor.fetchone()[0] or 0)

        #Shortest Description
        cursor.execute("""
            SELECT LENGTH(description), source_id, job_title 
            FROM jobs 
            ORDER BY LENGTH(description) ASC LIMIT 1
        """)
        shortest = cursor.fetchone()

        # 5. Longest Description
        cursor.execute("""
            SELECT LENGTH(description), source_id, job_title 
            FROM jobs 
            ORDER BY LENGTH(description) DESC LIMIT 1
        """)
        longest = cursor.fetchone()

        # Print Output Format
        print("--- 🔍 DATA QUALITY REPORT ---")
        print(f"📈 Total Records: {total_records}")
        print(f"❓ Missing Values -> job_title: {nulls[0]}, company: {nulls[1]}, description: {nulls[2]}")
        print(f"📝 Avg Description Length: {avg_len} chars")
        print(f"⚠️  Shortest Description: {shortest[0]} chars")
        print(f"   ↳ source_id: {shortest[1]} | job_title: {shortest[2]}")
        print(f"🚨 Longest Description: {longest[0]} chars")
        print(f"   ↳ source_id: {longest[1]} | job_title: {longest[2]}")

    except Exception as e:
        print(f"❌ Profiler failed: {e}")
    finally:
        if conn:
            conn.close()