import os
from dotenv import load_dotenv
import requests
import pandas as pd
import json

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
metadata = json.load(open(os.path.join(script_dir, "dw_design.json"), "r", encoding="utf-8"))
print(metadata["column-metadata"])

load_dotenv()  # this will load variables from .env into os.environ

## LOAD IN THE DW TOKEN
DW_TOKEN = os.getenv("DW_TOKEN")
if DW_TOKEN is None:
    raise ValueError("DW_TOKEN not found in .env file")

## LOAD IN THE DATA AND TOPOJSONS
opstillingskredse = pd.read_json(os.path.join(script_dir, "opstillingskredse.json"))
storkredse = pd.read_json(os.path.join(script_dir, "storkredse.json"))

## DEFINE THE FUNCTIONS TO CREATE THE CHARTS, TABLES AND MAPS

def create_status_tables(row, folder_id):
    navn = row['storkreds_navn'] if 'storkreds_navn' in row else row['opstillingskreds_navn']

    url = "https://api.datawrapper.de/v3/charts"
    headers = {
        "Authorization": "Bearer " + DW_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": "Sådan stemte " + navn ,
        "type": "tables",
        "folderId": folder_id,
        "metadata" : metadata["status-table-metadata"],
        'language': 'da-DK'
    }

    response = requests.post(url, headers=headers, json=data)
    return response

def create_stemmer_tables(row, folder_id):
    navn = row['storkreds_navn'] if 'storkreds_navn' in row else row['opstillingskreds_navn']

    url = "https://api.datawrapper.de/v3/charts"
    headers = {
        "Authorization": "Bearer " + DW_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": "Sådan stemte " + navn ,
        "type": "tables",
        "folderId": folder_id,
        "metadata" : metadata["stemme-table-metadata"],
        'language': 'da-DK'
    }

    response = requests.post(url, headers=headers, json=data)
    return response

def create_bar_charts(row, chart_folder_id):
    navn = row['storkreds_navn'] if 'storkreds_navn' in row else row['opstillingskreds_navn']

    url = "https://api.datawrapper.de/v3/charts"
    headers = {
        "Authorization": "Bearer " + DW_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": "Sådan stemte " + navn,
        "type": "column-chart",
        "folderId": chart_folder_id,
        "metadata" : metadata["column-metadata"],  
        'language': 'da-DK'
        }

    response = requests.post(url, headers=headers, json=data)
    return response

def create_maps(row, map_folder_id):

    url = "https://api.datawrapper.de/v3/charts"
    headers = {
        "Authorization": "Bearer " + DW_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": "Sådan stemte " + (row['storkreds_navn'] if 'storkreds_navn' in row else row['opstillingskreds_navn']),
        "type": "d3-maps-choropleth",
        "folderId": map_folder_id,
        "metadata" : {
            "describe": {
                "intro": "Her kan du se, hvordan der blev stemt i " + (row['storkreds_navn'] if 'storkreds_navn' in row else row['opstillingskreds_navn']) + " ved folketingsvalget 24. marts 2026.",
                "source-name": "Valgdata fra valg.dk",
                "source-url": "https://www.valg.dk",
                "byline": "Laura Bejder Jensen"}
        },
        'language': 'da-DK'
    }

    response = requests.post(url, headers=headers, json=data)
    return response

# topojson can only be added after the map is created, otherwise we get a 400 error

def create_graphics(data, geo, status_folder_id, chart_folder_id, map_folder_id, candidate_votes_folder_id):
    for index, row in data.iterrows():
        # # Create status table
        # status_table_response = create_status_tables(row, status_folder_id)
        # if status_table_response.status_code == 201:
        #     table_id = status_table_response.json()['id']
        #     data.at[index, 'table_id'] = table_id
        #     print(f"Created table for {row.get('storkreds_navn', row.get('opstillingskreds_navn'))}: {table_id}")
        # else:
        #     print(f"Failed to create table: {status_table_response.status_code} - {status_table_response.text}")
            
        # # create tables for candidate votes
        # candidate_votes_response = create_stemmer_tables(row, candidate_votes_folder_id)
        # if candidate_votes_response.status_code == 201:
        #     candidate_votes_table_id = candidate_votes_response.json()['id']
        #     data.at[index, 'candidate_votes_table_id'] = candidate_votes_table_id
        #     print(f"Created candidate votes table for {row.get('storkreds_navn', row.get('opstillingskreds_navn'))}: {candidate_votes_table_id}")
        # else:
        #     print(f"Failed to create candidate votes table: {candidate_votes_response.status_code} - {candidate_votes_response.text}")
        #     continue

        # # Create bar chart
        # chart_response = create_bar_charts(row, chart_folder_id)
        # if chart_response.status_code == 201:
        #     chart_id = chart_response.json()['id']
        #     data.at[index, 'chart_id'] = chart_id
        #     print(f"Created chart for {row.get('storkreds_navn', row.get('opstillingskreds_navn'))}: {chart_id}")
        # else:
        #     print(f"Failed to create chart: {chart_response.status_code} - {chart_response.text}")
            
        # Create map
        map_response = create_maps(row, map_folder_id)
        if map_response.status_code == 201:
            map_id = map_response.json()['id']
            data.at[index, 'map_id'] = map_id
            print(f"Created map for {row.get('storkreds_navn', row.get('opstillingskreds_navn'))}: {map_id}")
        else:
            print(f"Failed to create map: {map_response.status_code}")
            continue

        url = f"https://api.datawrapper.de/v3/charts/{map_id}"
        headers = {
            "Authorization": f"Bearer {DW_TOKEN}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Pretty print the full metadata
        chart = response.json()
        print(json.dumps(chart["metadata"], indent=2)) 

        # save the chart ids in the json file
        with open(os.path.join(script_dir, f"{geo}.json"), "w", encoding="utf-8") as f:
            json.dump(data.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


for col in ["table_id", "chart_id", "map_id", "candidate_votes_table_id"]:
    storkredse[col] = storkredse[col].astype("object")

create_graphics(storkredse, "storkredse", status_folder_id = "392410", chart_folder_id="392411", map_folder_id="390777", candidate_votes_folder_id="392412")
print("Finished creating graphics for storkredse.")

for col in ["table_id", "chart_id", "map_id", "candidate_votes_table_id"]:
    opstillingskredse[col] = opstillingskredse[col].astype("object")
create_graphics(opstillingskredse, "opstillingskredse", status_folder_id = "392527", chart_folder_id="392528", map_folder_id="390784", candidate_votes_folder_id="392530")
print("Finished creating graphics for opstillingskredse.")
