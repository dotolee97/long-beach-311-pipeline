import time
from datetime import date
from pathlib import Path

import requests

DATASET_URL = "https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests"
RECORDS_URL = DATASET_URL + "/records"
EXPORT_URL = DATASET_URL + "/exports/jsonl"
RAW_DIR = Path("data/raw")


def get_total_count():
    """Ask the API how many rows the dataset has, without downloading any rows."""
    response = requests.get(RECORDS_URL, params={"limit": 0}, timeout=30)
    response.raise_for_status()
    return response.json()["total_count"]


def download_export():
    """Download the full dataset as JSON Lines into data/raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / f"service_requests_{date.today()}.jsonl"

    start = time.time()
    with requests.get(EXPORT_URL, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    seconds = time.time() - start

    size_mb = output_path.stat().st_size / 1_000_000
    print(f"Downloaded {size_mb:.1f} MB to {output_path} in {seconds:.1f} seconds")
    return output_path


def count_lines(path):
    """Count records in a JSON Lines file (one record per line)."""
    with open(path, "rb") as f:
        return sum(1 for line in f)


if __name__ == "__main__":
    expected = get_total_count()
    path = download_export()
    actual = count_lines(path)
    print("Expected rows (total_count):", expected)
    print("Rows in file:", actual)
    if expected == actual:
        print("MATCH")
    else:
        print("MISMATCH")
        print("Difference:", expected - actual)