import requests

BASE_URL = "https://data.longbeach.gov/api/explore/v2.1/catalog/datasets/service-requests/records"

params = {
    "limit": 100,
    "offset": 9900,
    "order_by": "casenumber",
}

response = requests.get(BASE_URL, params=params, timeout=30)
print("HTTP status:", response.status_code)

if response.status_code != 200:
    print(response.text)
else:
    data = response.json()
    print("Total rows:", data["total_count"])
    for record in data["results"]:
        print(record["casenumber"], record["type"], record["status"], record["createddate"])