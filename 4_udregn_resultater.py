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

# convert Danish characters to ASCII for filenames
def danish_to_ascii_filename(text):
    """Convert Danish characters to ASCII equivalents for safe filenames."""
    danish_to_ascii = {
        'æ': 'ae', 'ø': 'o', 'å': 'aa',
        'Æ': 'AE', 'Ø': 'O', 'Å': 'AA'
    }
    text = text.lower()
    for danish, ascii_equiv in danish_to_ascii.items():
        text = text.replace(danish, ascii_equiv)
    return text.replace(' ', '_')

# standardiser partinavne og -bogstaver
def standardize_party_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map to Altinget party names/letters based on config."""
    bogstav_to_navn = {p["listebogstav"]: p["navn"] for p in partier_info}
    bogstav_to_bogstav = {p["listebogstav"]: p["bogstav"] for p in partier_info}

    df["parti"] = df["parti_bogstav"].map(bogstav_to_navn).fillna(df["parti_bogstav"])
    df["bogstav"] = df["parti_bogstav"].map(bogstav_to_bogstav).fillna(df["parti_bogstav"])
    return df

# ----------------------------
# Definer centrale funktioner
# ----------------------------

# Udregn procentfordeling
def udregn_procenter(df: pd.DataFrame) -> pd.DataFrame:
    """Udregn procentfordeling af stemmer for hver parti i hver opstillingskreds."""
    df = df.copy()

    total_gyldige_stemmer = df.groupby("afstemningsområde")["total_gyldige_stemmer"].first().sum() # find det samlede antal gyldige stemmer for opstillingskredsen

    # group data by party and sum votes and valid votes
    df = (df
        .groupby("parti")
        .agg({
            "stemmer": "sum",
            "total_gyldige_stemmer": lambda x: total_gyldige_stemmer # total gyldige stemmer should be the same for all rows in the same opstillingskreds
        })
        .reset_index()
        )

    df["procent"] = (df["stemmer"] / df["total_gyldige_stemmer"]) * 100

    # #check if the percentages sum to 100, if not, raise an error
    # procent_sum = df["procent"].sum()
    # if the sum is 0, we can skip the check to avoid division by zero errors
    # if procent_sum == 0:
    #     return df
    # elif not (99.9 <= procent_sum <= 100.1):
    #     raise ValueError(f"Procenterne summerer ikke til 100% (summerer til {procent_sum:.2f}%)")

    df["parti_bogstav"] = df["parti"].map({p["navn"]: p["bogstav"] for p in partier_info}).fillna(df["parti"]) # map partinavne til bogstaver, hvis muligt
    df = df[["parti_bogstav", "parti", "procent"]] # ændr rækkefølgen af kolonner for bedre læsbarhed

    # add 2022 results for comparison
    return df

def udregn_status(df: pd.DataFrame) -> pd.DataFrame:
    total_valgsteder = df["afstemningsområde"].nunique()
    # find the number where resultat_art is ForeløbigOptælling or Fintælling
    foreløbig_optælling = df[df["resultat_art"].isin(["ForeløbigOptælling", "Fintælling"])]["afstemningsområde"].nunique()
    done_share = f"{foreløbig_optælling} ud af {total_valgsteder}"
    # create a dataframe with the status
    status_df = pd.DataFrame({
        "Optalte valgsteder": [foreløbig_optælling]
    })
    return status_df

# ----------------------------
# Kald funktionerne for hver opstillingskreds, storkreds og nationalt
# ----------------------------

if __name__ == "__main__":
    
    # -----------------------------
    # Process hver opstillingskreds
    for opstillingskreds in resultater_partier["opstillingskreds"].unique():
        df_opstillingskreds = resultater_partier[resultater_partier["opstillingskreds"] == opstillingskreds]
        opstillingskreds_id = df_opstillingskreds["opstillingskreds_dagi_id"].iloc[0]
        # get status for the opstillingskreds
        status = udregn_status(df_opstillingskreds)
        status.to_csv(f"data/struktureret/opstillingskredse/status/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}_status.csv", index=False)
        try:
            res = udregn_procenter(df_opstillingskreds)
            
            #turn into a dataframe and save as csv
            res_df = pd.DataFrame(res)
            res_df.to_csv(f"data/struktureret/opstillingskredse/procenter/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}.csv", index=False)
        except ValueError as e:
            print(f"Warning: {opstillingskreds} - {e}")

    # ----------------------
    # Process hver storkreds
    for storkreds in resultater_partier["storkreds"].unique():
        df_storkreds = resultater_partier[resultater_partier["storkreds"] == storkreds]
        storkreds_id = df_storkreds["storkreds_nummer"].iloc[0]

        # få status på stemmeoptællingen for hver storkreds
        status = udregn_status(df_storkreds)
        status.to_csv(f"data/struktureret/storkredse/status/{storkreds_id}_{danish_to_ascii_filename(storkreds)}_status.csv", index=False)

        try:
            res = udregn_procenter(df_storkreds)
            res_df = pd.DataFrame(res)
            res_df.to_csv(f"data/struktureret/storkredse/procenter/{storkreds_id}_{danish_to_ascii_filename(storkreds)}.csv", index=False)
        except ValueError as e:
            print(f"Warning: storkreds {storkreds} - {e}")

    # -----------------
    # Process nationalt

    # få status på stemmeoptællingen for nationalt
    status = udregn_status(resultater_partier)
    status.to_csv(f"data/struktureret/nationalt/status/nationalt_status.csv", index=False)

    # Udregn hvor mange procent af stemmerne, hvert parti har fået på landsplan
    try:
        res = udregn_procenter(resultater_partier)
        res_df = pd.DataFrame(res)
        res_df.to_csv(f"data/struktureret/nationalt/procenter/nationalt_procenter.csv", index=False)
    except ValueError as e:
        print(f"Warning: national results - {e}")
