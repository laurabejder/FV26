import pandas as pd
import os
import glob
import json
import datetime
from pathlib import Path

from config import FROM_PATH, TO_PATH, FOLDERS

# find alle de rå datafiler
def kombiner_resultater(from_path, to_path, data_type):
    os.makedirs(to_path, exist_ok=True) # Opret output-mappen, hvis den ikke findes
    
    file_pattern = os.path.join(from_path, data_type, "*.json") # Find alle json-filer i den angivne mappe
    all_files = glob.glob(file_pattern)

    return all_files 

# Valgresultater
def get_resultater(from_path=FROM_PATH, to_path=TO_PATH, folders=FOLDERS, *_unused):
    files = kombiner_resultater(from_path, to_path, folders[0])
    partier, kandidater = [], []

    for file in files:
        try:
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
        
        # define base structure for each entry (what columns do we want in the data)
        base = {
            "storkreds_nummer": data.get("Storkredsnummer"),
            "storkreds": data.get("Storkreds"), 
            "opstillingskreds_dagi_id": data.get("OpstillingskredsDagiId"),
            "opstillingskreds": data.get("Opstillingskreds"),
            "afstemningsområde_dagi_id": data.get("AfstemningsområdeDagiId"),
            "afstemningsområde": data.get("Afstemningsområde"),
            "frigivelsestidspunkt": data.get("FrigivelsesTidspunktUTC"),
            "godkendelsestidspunkt": data.get("GodkendelsesTidspunktUTC"),
            "resultat_art": data.get("Resultatart"),
            "total_gyldige_stemmer": data.get("GyldigeStemmer"),
            "total_afgivne_stemmer": data.get("AfgivneStemmer"),
        }

        # if there are no results, add a placeholder entry
        if data.get("Resultatart") == "IngenResultater":
            partier.append({
                **base, "parti": None, "stemmer": 0, "listestemmer": 0,
                "difference_forrige_valg": 0
            })
            continue
        
        else:
            # Handle IndenforParti - these are party objects with candidate arrays
            for parti in (data.get("IndenforParti") or []):
                partier.append({
                    **base,
                    "parti": parti.get("PartiNavn"),
                    "parti_id": parti.get("PartiId"),
                    "parti_bogstav": parti.get("Bogstavbetegnelse"),
                    "stemmer": parti.get("Stemmer", 0),
                    "listestemmer": parti.get("Listestemmer", 0),
                    "difference_forrige_valg": parti.get("StemmerDifferenceFraForrigeValg", 0),
                })

                # Process candidates for this party
                for kandidat in (parti.get("Kandidater") or []):
                    kandidater.append({
                        **base,
                        "kandidat": kandidat.get("Stemmeseddelnavn"),
                        'kandidat_id': kandidat.get("Id"),
                        "parti": parti.get("PartiNavn"),
                        "parti_id": parti.get("PartiId"),
                        "parti_bogstav": parti.get("Bogstavbetegnelse"),
                        "stemmer": kandidat.get("Stemmer", 0),
                    })

            # Handle UdenforParti - these are candidate objects directly (no party wrapper)
            udenfor_parti_candidates = data.get("UdenforParti") or []
            if udenfor_parti_candidates:
                # Add a single party entry for all "Udenfor parti" candidates
                total_udenfor_parti_stemmer = sum(kandidat.get("Stemmer", 0) for kandidat in udenfor_parti_candidates)
                partier.append({
                    **base,
                    "parti": "Udenfor parti",
                    "parti_id": None,
                    "parti_bogstav": "UP",
                    "stemmer": total_udenfor_parti_stemmer,
                    "listestemmer": 0,
                    "difference_forrige_valg": 0,
                })

                # Process each candidate outside parties
                for kandidat in udenfor_parti_candidates:
                    kandidater.append({
                        **base,
                        "kandidat": kandidat.get("Stemmeseddelnavn"),
                        'kandidat_id': kandidat.get("Id"),
                        "parti": "Udenfor parti",
                        "parti_id": None,
                        "parti_bogstav": "UP",
                        "stemmer": kandidat.get("Stemmer", 0),
                    })

    return partier, kandidater

partier, kandidater = get_resultater(FROM_PATH, TO_PATH)


df_partier = pd.DataFrame(partier)
df_kandidater = pd.DataFrame(kandidater)


# Convert datetime columns (dd-mm-yyyy hh:mm:ss), coercing invalid/missing values
for df in (df_partier, df_kandidater):
    for col in ("frigivelsestidspunkt", "godkendelsestidspunkt"):
        if col in df:
            df[col] = pd.to_datetime(df[col], format="%d-%m-%Y %H:%M:%S", errors="coerce")

if df_partier.empty:
    # save an empty dataframe with the correct columns
    df_partier = pd.DataFrame(columns=[
        "storkreds_nummer", "storkreds", "opstillingskreds_dagi_id", "opstillingskreds", "afstemningsområde", "afstemningsområde_dagi_id",
        "frigivelsestidspunkt", "godkendelsestidspunkt", "resultat_art",
        "total_gyldige_stemmer", "total_afgivne_stemmer",
        "parti", "parti_id", "parti_bogstav", "stemmer", "listestemmer",
        "difference_forrige_valg"
    ])

outdir = Path(TO_PATH)
outdir.mkdir(parents=True, exist_ok=True)
df_partier.to_csv(outdir / "resultater_partier.csv", index=False)

# check if df_kv_kandidater is not empty before saving
if df_kandidater.empty:
    # save an empty dataframe with the correct columns
    df_kandidater = pd.DataFrame(columns=[
        "storkreds_nummer", "storkreds", "opstillingskreds_dagi_id", "opstillingskreds", "afstemningsområde", "afstemningsområde_dagi_id",
        "frigivelsestidspunkt", "godkendelsestidspunkt", "resultat_art",
        "total_gyldige_stemmer", "total_afgivne_stemmer",
        "kandidat", "kandidat_id", "parti", "parti_id", "parti_bogstav", "stemmer"
    ])

df_kandidater.to_csv(outdir / "resultater_kandidater.csv", index=False)
