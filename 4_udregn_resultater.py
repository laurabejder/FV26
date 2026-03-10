import json
from pathlib import Path
import pandas as pd
from config import PARTIER_INFO

# pop ups!

# ----------------------------
# Filstier og load af datafiler
# ----------------------------

BASE_PATH = Path("data/struktureret/valgresultater")
NATIONAL_DIR = BASE_PATH / "nationalt"
STORKREDS_DIR = BASE_PATH / "storkredse"
OPSTILLINGSKREDS_DIR = BASE_PATH / "opstillingskredse"

# Load filen med partiinformation, så vi senere kan standardisere partinavne og -bogstaver
with open(PARTIER_INFO, "r", encoding="utf-8") as f:
    partier_info = json.load(f)

# Hent valgresultaterne for FV26 på kandidniveau
resultater_kandidater = (
    pd.read_csv("data/struktureret/resultater_kandidater.csv")
    .drop_duplicates()
    .reset_index(drop=True)
)

# Hent valgresultaterne for FV26 på partiniveau
resultater_partier = (
    pd.read_csv("data/struktureret/resultater_partier.csv")
    .drop_duplicates()
    .reset_index(drop=True)
)

# ----------------------------
# Definer støttende funktioner
# ----------------------------

# fjern ufærdige resultater
def resultater_findes(data):
    return data[data["resultat_art"] != 'IngenResultater']

# standardiser partinavne og -bogstaver
def standardize_party_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map to Altinget party names/letters based on config."""
    bogstav_to_navn = {p["listebogstav"]: p["navn"] for p in partier_info}
    bogstav_to_bogstav = {p["listebogstav"]: p["bogstav"] for p in partier_info}

    df["parti"] = df["parti_bogstav"].map(bogstav_to_navn).fillna(df["parti_bogstav"])
    df["bogstav"] = df["parti_bogstav"].map(bogstav_to_bogstav).fillna(df["parti_bogstav"])
    return df

