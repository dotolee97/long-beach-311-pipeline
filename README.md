# Long Beach 311 Service Requests Pipeline

A data pipeline that pulls the City of Long Beach's 311 service request data (Go Long Beach app) from the city's open data API and loads it into PostgreSQL. Built with Python, SQL, and Docker.

**Status: in progress.** Extract and raw load work. Cleaning, validation, and analysis are next.

## Progress

- [x] Explore the data source ([notes](docs/data_source.md))
- [x] PostgreSQL in Docker
- [x] Extract: download the full dataset from the API
- [x] Load: load raw records into Postgres
- [ ] Staging: clean, typed table with SQL
- [ ] Data quality checks
- [ ] One command to run the whole pipeline
- [ ] Tests
- [ ] Analysis queries and dashboard

## How it works (so far)

```
Long Beach Open Data API
        |
        |  pipeline/extract.py   download full export, check row count
        v
data/raw/service_requests_YYYY-MM-DD.jsonl
        |
        |  pipeline/load.py      COPY into Postgres, check row count
        v
PostgreSQL (Docker): raw.service_requests
```

## Data source

- Dataset: [Go Long Beach Service Requests](https://data.longbeach.gov/explore/assets/service-requests/view/), published by the City of Long Beach
- About 363,000 requests since 2020-09-21, updated every 4 hours
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data provided by the City of Long Beach.

More detail on columns, statuses, and data quality issues: [docs/data_source.md](docs/data_source.md)

## Tech

- Python (requests, psycopg, python-dotenv)
- PostgreSQL 17 in Docker (Docker Compose)
- SQL

## Setup

You need Git, Python 3, and Docker Desktop.

1. Clone the repo:
   ```
   git clone https://github.com/dotolee97/long-beach-311-pipeline.git
   cd long-beach-311-pipeline
   ```

2. Create your `.env` from the template and set your own password:
   ```
   cp .env.example .env
   ```
   (Windows PowerShell: `Copy-Item .env.example .env`)

3. Start Postgres:
   ```
   docker compose up -d
   ```

4. Create the raw table:
   ```
   docker compose exec -T db psql -U lb311 -d lb311 -v ON_ERROR_STOP=1 < sql/raw/001_create_raw_tables.sql
   ```
   (Windows PowerShell: `Get-Content sql\raw\001_create_raw_tables.sql | docker compose exec -T db psql -U lb311 -d lb311 -v ON_ERROR_STOP=1`)

5. Set up Python:
   ```
   python -m venv .venv
   ```
   Activate it (Windows: `.\.venv\Scripts\Activate.ps1`, macOS/Linux: `source .venv/bin/activate`), then:
   ```
   python -m pip install -r requirements.txt
   ```

## Run

```
python pipeline/extract.py
python pipeline/load.py
```

## Results so far

Measured on my laptop, 2026-11-23:

| Step | Result |
|---|---|
| Extract | 141.4 MB, 363,250 rows, 59.4 seconds. Row count matched the API's total_count. |
| Load | 363,250 rows in about 2 seconds using COPY. Row count matched the file. |
| Rerun load | Still 363,250 rows, and every row has the newer load time. |

## Design decisions

- **Full export instead of paging.** The API's `/records` endpoint only returns 100 rows per request and can't page past row 10,000. The `/exports/jsonl` endpoint downloads everything in one request.
- **Full refresh.** Each run reloads the whole dataset. It takes about a minute, and the data has no last-updated column, so loading only changes could miss records that changed.
- **Raw data saved as JSON Lines.** Same structure the API sends, one record per line.
- **Raw table stores each record unchanged as JSONB**, plus the source file name and load time. Cleaning happens in a separate staging step, so the data can be reprocessed without downloading again.
- **Load runs in one transaction** (TRUNCATE + COPY). Running it twice doesn't duplicate rows, and if it fails partway the previous load stays in place.

## Troubleshooting

- **"password authentication failed"**: if you have PostgreSQL installed directly on your computer, it's probably using port 5432. This project's Postgres runs on port **5433** (set by `POSTGRES_PORT` in `.env`) to avoid that.
- **Changed the password in `.env` and it stopped working**: Postgres only reads `POSTGRES_PASSWORD` the first time the database volume is created. Either change it with `ALTER USER`, or reset the database with `docker compose down -v` (this deletes the data).