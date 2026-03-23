import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

DW_TOKEN = os.getenv("DW_TOKEN")
if DW_TOKEN is None:
    raise ValueError("DW_TOKEN not found in .env file")

storkredse = json.load(open("storkredse.json", "r", encoding="utf-8"))
opstillingskredse = json.load(open("opstillingskredse.json", "r", encoding="utf-8"))

hele_landet = ["TSMB4","6FZCA","vfKdN","YWrYe","qe2sm","Z3bMs","FeCJO"]


print("Publishing charts...")

for storkreds in storkredse:
    charts = [
        storkreds.get("chart_id"),
        storkreds.get("table_id"),
        storkreds.get("map_id"),
        storkreds.get("candidate_votes_table_id"),
    ]

    for chart_id in charts:
        print(f"Publishing chart with id {chart_id}")
        url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"

        payload = { "callWebhooks": True }
        headers = {
                "Authorization": f"Bearer {DW_TOKEN}",
                "accept": "*/*",
                "content-type": "application/json"
            }

        response = requests.post(url, json=payload, headers=headers)
        if response.ok:
            print(f"Published {chart_id}")
        else:
            print(f"Failed {chart_id}: {response.status_code} {response.text}")


for opstillingskreds in opstillingskredse:
    charts = [
        opstillingskreds.get("chart_id"),
        opstillingskreds.get("table_id"),
        opstillingskreds.get("map_id"),
        opstillingskreds.get("candidate_votes_table_id"),
    ]

    for chart_id in charts:
        print(f"Publishing chart with id {chart_id}")
        url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"

        payload = { "callWebhooks": True }
        headers = {
                "Authorization": f"Bearer {DW_TOKEN}",
                "accept": "*/*",
                "content-type": "application/json"
            }

        response = requests.post(url, json=payload, headers=headers)
        if response.ok:
            print(f"Published {chart_id}")
        else:
            print(f"Failed {chart_id}: {response.status_code} {response.text}")


for chart_id in hele_landet:
        print(f"Publishing chart with id {chart_id}")
        url = f"https://api.datawrapper.de/v3/charts/{chart_id}/publish"

        payload = { "callWebhooks": True }
        headers = {
                "Authorization": f"Bearer {DW_TOKEN}",
                "accept": "*/*",
                "content-type": "application/json"
            }

        response = requests.post(url, json=payload, headers=headers)
        if response.ok:
            print(f"Published {chart_id}")
        else:
            print(f"Failed {chart_id}: {response.status_code} {response.text}")