import os
import time

import psycopg
from dotenv import load_dotenv

from extract import RAW_DIR, count_lines

load_dotenv()


def get_connection():
    """Connect to the Postgres database running in Docker."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def latest_raw_file():
    """Find the newest downloaded file in data/raw/."""
    files = sorted(RAW_DIR.glob("service_requests_*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No raw files in {RAW_DIR}. Run extract.py first.")
    return files[-1]


def load_raw(path):
    """Replace everything in raw.service_requests with the records from one JSONL file."""
    start = time.time()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE raw.service_requests")
            with cur.copy("COPY raw.service_requests (payload, source_file) FROM STDIN") as copy:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            copy.write_row((line, path.name))
            cur.execute("SELECT count(*) FROM raw.service_requests")
            loaded = cur.fetchone()[0]
    seconds = time.time() - start
    print(f"Loaded {loaded} rows from {path.name} in {seconds:.1f} seconds")
    return loaded


if __name__ == "__main__":
    path = latest_raw_file()
    expected = count_lines(path)
    loaded = load_raw(path)
    print("Lines in file:", expected)
    print("Rows in table:", loaded)
    if expected == loaded:
        print("MATCH")
    else:
        print("MISMATCH")
        print("Difference:", expected - loaded)