import sqlite3
import time
import os
import re
from typing import List, Tuple, Dict, Any
import ollama  # Uses your local downloaded models

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────

# Swap this with any model you have downloaded (e.g., "llama3.1", "phi4", "mistral")
LOCAL_MODEL_NAME    = "deepseek-r1:1.5b" 
BATCH_SIZE          = 5   # Local models have smaller context windows; 5 keeps parsing accurate
MAX_RETRIES         = 3
INITIAL_RETRY_DELAY = 2.0

SYSTEM_INSTRUCTION = (
    "You are a strict technical classification pipeline. "
    "Given a list of job descriptions, extract only the technical stack for each job. "
    "Respond with one line per job in exactly this format:\n"
    "ID:<id> | <comma-separated technologies>\n"
    "Include only real technologies, languages, frameworks, tools, and platforms. "
    "Do not include soft skills, benefits, or non-technical terms."
)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def build_batch_prompt(jobs: List[Tuple[int, str]]) -> str:
    lines = ["Extract comma-separated technologies for each job ID below:\n"]
    for job_id, desc in jobs:
        # Clean white spaces and clip to save local VRAM context processing
        compressed = re.sub(r'\s+', ' ', desc).strip()[:600]
        lines.append(f"ID:{job_id} | {compressed}")
    return "\n".join(lines)


def parse_response(response_text: str) -> Dict[int, str]:
    results = {}
    
    # Clean up DeepSeek-R1 thinking tokens if present so they don't break regex parsing
    clean_text = re.sub(r'<thought>.*?</thought>', '', response_text, flags=re.DOTALL)
    
    for line in clean_text.strip().splitlines():
        match = re.search(r"ID:\s*(\d+)\s*[|:]\s*(.+)", line, re.IGNORECASE)
        if match:
            job_id = int(match.group(1))
            tech   = re.sub(r'[*_`]', '', match.group(2)).strip()
            results[job_id] = tech
    return results


# ─────────────────────────────────────────────
#  Main Function
# ─────────────────────────────────────────────

def tag_data(db_url: str):
    """
    Reads the `jobs` table from the SQLite database.
    Populates the `tech_stack` column completely OFFLINE using your local Ollama models.
    """
    start_time = time.time()

    try:
        conn   = sqlite3.connect(db_url)
        cursor = conn.cursor()

        # Ensure tech_stack column exists
        try:
            cursor.execute("SELECT tech_stack FROM jobs LIMIT 1;")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE jobs ADD COLUMN tech_stack TEXT;")
            conn.commit()

        # Fetch only untagged rows
        cursor.execute(
            "SELECT id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = '';"
        )
        rows = cursor.fetchall()

        if not rows:
            print("✨ All rows already tagged — nothing to do.")
            conn.close()
            return time.time() - start_time

        print(f"📦 Found {len(rows)} untagged jobs. Processing locally via Ollama ({LOCAL_MODEL_NAME})...\n")

        # ── Batch loop ─────────────────────────────────────────
        for batch_index, i in enumerate(range(0, len(rows), BATCH_SIZE)):
            batch  = rows[i : i + BATCH_SIZE]
            prompt = build_batch_prompt(batch)

            attempt       = 0
            current_delay = INITIAL_RETRY_DELAY
            response_text = None

            # ── Retry loop ─────────────────────────────────────
            while attempt < MAX_RETRIES:
                try:
                    # Querying your local CLI model engine
                    response = ollama.chat(
                        model=LOCAL_MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_INSTRUCTION},
                            {"role": "user", "content": prompt}
                        ],
                        options={
                            "temperature": 0.1  # Keep it deterministic
                        }
                    )

                    response_text = response['message']['content']
                    parsed        = parse_response(response_text)

                    # Simple validation checkpoint
                    if len(parsed) < len(batch):
                        raise ValueError(
                            f"Mismatch: Batch had {len(batch)} items but local model parsed {len(parsed)}"
                        )
                    break  # Success!

                except Exception as e:
                    attempt += 1
                    print(f"[Batch {batch_index}] Attempt {attempt} failed: Local engine error — {e}")
                    if attempt >= MAX_RETRIES:
                        break
                    time.sleep(current_delay)
                    current_delay *= 1.5

            if response_text is None:
                print(f"[Batch {batch_index}] ❌ Skipping batch after max retries.\n")
                continue

            # ── Write results to DB ────────────────────────────
            parsed    = parse_response(response_text)
            db_writes = []

            for job_id, _ in batch:
                tech = parsed.get(job_id, "None Detected")
                db_writes.append((tech, job_id))
                print(f"🖥️  [Local AI] Analyzed Job {job_id}: {tech}")

            cursor.executemany(
                "UPDATE jobs SET tech_stack = ? WHERE id = ?;", db_writes
            )
            conn.commit()
            print()

        conn.close()

    except Exception as e:
        print(f"❌ Critical error: {e}")
        return time.time() - start_time

    return time.time() - start_time


# ─────────────────────────────────────────────
#  Quality Measurement
# ─────────────────────────────────────────────

def run_quality_measurement(db_url: str):
    print("📊 --- Local Extraction Quality Evaluation ---")
    try:
        conn   = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT id, tech_stack FROM jobs WHERE tech_stack IS NOT NULL;")
        records = cursor.fetchall()
        conn.close()

        if not records:
            print("❌ No tagged records to evaluate.")
            return

        total    = len(records)
        failures = 0
        all_tags = []

        for _, tech_str in records:
            if not tech_str or "none detected" in tech_str.lower():
                failures += 1
                continue
            tags = [t.strip().lower() for t in tech_str.split(",") if t.strip()]
            all_tags.extend(tags)

        unique_tags = set(all_tags)
        success_pct = ((total - failures) / total) * 100

        print(f"  Total records evaluated    : {total}")
        print(f"  Extraction success rate    : {success_pct:.1f}%")
        print(f"  Total tech tags extracted  : {len(all_tags)}")
        print(f"  Unique technologies found  : {len(unique_tags)}")
        if total > 0:
            print(f"  Avg tags per job           : {len(all_tags)/total:.1f}")
        print("─" * 44)

    except Exception as e:
        print(f"⚠️  Quality check failed: {e}")


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

def main():
    TARGET_DB = "data/resources/jobs_d1.db"
    os.makedirs(os.path.dirname(TARGET_DB), exist_ok=True)

    if not os.path.exists(TARGET_DB):
        print(f"🔧 Creating mock database at '{TARGET_DB}'...")
        conn   = sqlite3.connect(TARGET_DB)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS jobs "
            "(id INTEGER PRIMARY KEY, description TEXT, tech_stack TEXT);"
        )
        cursor.executemany(
            "INSERT INTO jobs (description, tech_stack) VALUES (?, ?);",
            [
                ("Senior Java engineer with Spring Boot, microservices, and Postgres.", None),
                ("Frontend developer with React, Next.js, and Tailwind CSS.", None),
                ("Python cloud engineer with AWS, Docker, and Snowflake.", None),
                ("Manual QA analyst running regression scripts.", None),
            ]
        )
        conn.commit()
        conn.close()

    elapsed = tag_data(TARGET_DB)

    print("🏁 --- Final Statistics ---")
    print(f"  Time elapsed        : {elapsed:.2f}s")
    print(f"  Model Engine        : Ollama Local CLI ({LOCAL_MODEL_NAME})")
    print(f"  Cost footprint      : $0.00 (Fully Offline)\n")

    run_quality_measurement(TARGET_DB)


if __name__ == "__main__":
    main()