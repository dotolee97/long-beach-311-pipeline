# Data source notes: Go Long Beach service requests

Notes from exploring the dataset before building the pipeline. First explored 2026-10-30. Numbers below were refreshed on 2026-11-22.

## Source

- Portal: https://data.longbeach.gov (Opendatasoft, API v2.1)
- Dataset: Go Long Beach Service Requests (ID: `service-requests`)
- Records: `https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records`
- Metadata: same URL without `/records`
- No API key needed. Worked in the browser without one.
- 363,130 rows on 2026-11-22 (358,802 on 2026-10-30)
- Data starts 2020-09-21
- Published every 4 hours, automatically (from the metadata)
- Newest `createddate` on 11/22 was 11/22 1:34 AM Pacific
- License: CC BY 4.0. Need to credit the City of Long Beach in the README.

I go to CSULB, so I wanted to work with Long Beach data and see how the city handles requests from residents. Cypress, where I live, doesn't publish this kind of data.

## Columns

Source types are from the metadata. Postgres types are my choices.

| Column | Source type | Postgres type | Notes |
|---|---|---|---|
| casenumber | text | TEXT | Request ID. Metadata marks it as the unique id. Leading zeros (00346779). |
| type | text | TEXT | 24 categories |
| status | text | TEXT | 6 values, see below |
| createddate | datetime | TIMESTAMPTZ | UTC |
| closeddate | datetime | TIMESTAMPTZ | Null for New, In Progress, Duplicate |
| citydistrict_c | text | TEXT | Council district, e.g. "CD 9" |
| zipcode_c | text | TEXT | |
| geolocation | geo_point_2d | latitude, longitude (NUMERIC) | {"lon": ..., "lat": ...} |
| days_to_close | int | INTEGER | Rounds down (8.97 days shows as 8). Null if not closed. |
| age_open | int | INTEGER | Stale, not using it |
| escooter_issue_c | text | TEXT | E-Scooter only |
| escooter_operator_c | text | TEXT | E-Scooter only. Can be "Bird Rides;Lime" |
| observed_time | datetime | TIMESTAMPTZ | Always null so far, no description |

## Statuses

| Status | 2026-10-30 | 2026-11-22 | closeddate? |
|---|---|---|---|
| Closed | 277,923 | 281,366 | yes |
| Closed Referred | 57,239 | 58,119 | yes |
| In Progress | 16,393 | 16,186 | no |
| Cancelled | 2,957 | 2,957 | yes |
| Duplicate | 2,794 | 2,757 | no |
| New | 1,496 | 1,745 | no |
| Total | 358,802 | 363,130 | |

Totals match total_count both times.

Open = New or In Progress (17,931 on 11/22). I'm not using "closeddate is null" because that also picks up Duplicates (20,688 on 11/22). Duplicates and Cancelled are left out of time-to-close.

The data doesn't say which case a Duplicate is a copy of.

The metadata says status values are "Open, Closed, In Progress etc." but there is no "Open" status in the data.

## Types

24 types, counts add up to 363,130. Top 5 on 11/22:

| Type | Count |
|---|---|
| Dumped Items | 141,264 |
| Graffiti | 85,491 |
| E-Scooter | 49,032 |
| Street Repair | 17,182 |
| Tree Maintenance | 17,055 |

## Things I noticed

- Records change after they're created. Between 10/30 and 11/22, Duplicate went down by 37 and In Progress went down by 207, so cases move between statuses.
- age_open doesn't update. A case from 7/20 still said 4 days in October.
- Oldest open cases are from 2020. Case 00001011 has been "In Progress" since 2020-09-23. Probably abandoned, not really being worked on.
- Times are UTC. 2026-07-25 03:03 UTC is 7/24 in Long Beach, so daily counts need to convert to Pacific. The metadata timezone is America/Los_Angeles.
- Lots of E-Scooter cases close the same minute they're opened (Closed Referred). Averaging time-to-close across all types would make it look faster than it is.
- Default API order is random-ish. First page on 10/30 was July data. Need order_by when paging.
- Aggregate query without group_by returns the same row 10 times. Adding limit=1 fixes it.
- /records limits: max 100 rows per request, and offset + limit can't go past 10,000. Paging with offset only reaches the first 10,000 rows.
- /exports/jsonl downloads the whole dataset in one request. On 2026-11-23: 141.4 MB, 363,250 rows, 59.4 seconds. Row count matched total_count.
- Lowest casenumber is 00001008 (2020-09-21). There are gaps in case numbers, so casenumber is only used as an ID, not for counting.

## Where the numbers came from

- Columns and types: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests
  - Dataset metadata. The `fields` section lists every column and its type. Also has records_count, license, publish frequency, and earliest data point.
- Sample rows: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?limit=10
- Statuses: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?select=status,count(*)%20as%20n&group_by=status
  - Count per status. Adds up to the total row count, so every row has a status.
- Types: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?select=type,count(*)%20as%20n&group_by=type&order_by=n%20desc&limit=50
- Oldest open cases: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?where=closeddate%20is%20null&order_by=createddate&limit=3
- Freshness: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?select=max(createddate)%20as%20latest_created,max(closeddate)%20as%20latest_closed&limit=1
- Statuses with no close date: https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records?select=status,count(*)%20as%20n&where=closeddate%20is%20null&group_by=status
  - Only New, In Progress, and Duplicate show up. This is why "open" is defined by status and not by a missing closeddate.

## Still deciding

Full reload vs. only pulling changes. There's no last-updated column, so I can't just ask for changed records, and records do change (see statuses above). Undecided for now. I'll pick one when I write the extract code.

Ideas to check later:

- age_open might stop counting when a record was last changed. The oldest open case shows 2,066 days, which lines up with about 2026-05-21. If that's true, it could tell me which records changed recently. Not confirmed.
- The metadata has a `modified` timestamp that updates when the data changes. The pipeline could check it first and skip the run if nothing changed.