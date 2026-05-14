import os
import json
import sqlite3
from pathlib import Path

def load_all_jsons(input_dir, output_dir):
    #create the path if path doesnt exist
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "jobs_warehouse.db")

    # Initialize Database & Schema
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # using source key to prevent duplicate entries, if source_id already exists, the new entry will be ignored
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                source_id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                description TEXT,
                tech_stack TEXT
            )
        """)
        connection.commit()

        #  Process Files
        json_files = list(Path(input_dir).glob("*.json"))
        inserted_count = 0
        skipped_count = 0

        print("🥇 Gold:...")

        for json_path in json_files:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO jobs (source_id, job_title, company, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (data["source_id"], data["job_title"], data["company"], data["description"]),
                )
                
                if cursor.rowcount > 0:
                    print(f"✅ Inserted: {json_path.name}")
                    inserted_count += 1
                else:
                    print(f"⏭️ Skipped (duplicate): {json_path.name}")
                    skipped_count += 1

            except Exception as e:
                print(f"❌ Failed to load {json_path.name}: {e}")

        connection.commit()

    # 4. Final Summary
    print(f"\n📊 Gold Summary:\nTotal: {len(json_files)} | Inserted: {inserted_count} | Skipped: {skipped_count}")