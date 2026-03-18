import json
from pathlib import Path
import pandas as pd
from config import PARTIER_INFO

from pop_up_info import largest_party_colors, party_colors

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
resultater_partier = (pd.read_csv("data/struktureret/resultater_partier.csv")
    .drop_duplicates()
    .reset_index(drop=True)
)

valgte_kandidater = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vTxLGlQjnEd-RGHCbVNhWzxmTH9dL6TiNlJHMbeVSwolMSEZN6uV4pc45iLLF0xUym26XwrFiXVhFFr/pub?gid=0&single=true&output=csv")

resultater_opstillingskredse_2022 = pd.read_csv("data/resultater_2022/processed/opstillingskreds_resultater.csv")
resultater_storkredse_2022 = pd.read_csv("data/resultater_2022/processed/storkreds_resultater.csv")
resultater_nationalt_2022 = pd.read_csv("data/resultater_2022/processed/nationalt_resultater.csv")

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
def udregn_procenter(df: pd.DataFrame, resultater_2022: pd.DataFrame) -> pd.DataFrame:
    """Udregn procentfordeling af stemmer for hver parti i hver opstillingskreds."""
    df = df.copy()

    total_gyldige_stemmer = df.groupby("afstemningsområde")["total_gyldige_stemmer"].first().sum()
    df = (df
        .groupby("parti")
        .agg({
            "stemmer": "sum",
            "total_gyldige_stemmer": lambda x: total_gyldige_stemmer # total gyldige stemmer should be the same for all rows in the same opstillingskreds
        })
        .reset_index()
        )

    df["procent_26"] = round((df["stemmer"] / df["total_gyldige_stemmer"]) * 100, 1)

    #check if the percentages sum to 100, if not, raise an error
    procent_sum = df["procent_26"].sum()
    if procent_sum == 0: #if the sum is 0, we can skip the check to avoid division by zero errors
        return df
    elif not (99.9 <= procent_sum <= 100.1):
        raise ValueError(f"Procenterne summerer ikke til 100% (summerer til {procent_sum:.2f}%)")

    df["parti_bogstav"] = df["parti"].map({p["navn"]: p["bogstav"] for p in partier_info}).fillna(df["parti"]) # map partinavne til bogstaver, hvis muligt

    # join results from 2022
    df = df.merge(
        resultater_2022[["Partibogstav", "procent_22"]],
        left_on="parti_bogstav",
        right_on="Partibogstav",
        how="left"
    ).drop(columns=["Partibogstav"])

    df = df[["parti_bogstav", "parti", "procent_26", "procent_22"]] # ændr rækkefølgen af kolonner for bedre læsbarhed

    # add 2022 results for comparison
    return df

def udregn_status(df: pd.DataFrame) -> pd.DataFrame:
    # find the number where resultat_art is ForeløbigOptælling or Fintælling
    foreløbig_optælling = df[df["resultat_art"].isin(["ForeløbigOptælling", "Fintælling"])]["afstemningsområde"].nunique()
    # create a dataframe with the status
    status_df = pd.DataFrame({
        "Optalte valgsteder": [foreløbig_optælling]
    })
    return status_df


def udregn_stoerste_parti(df: pd.DataFrame, geo_niveau, geo_id) -> pd.DataFrame:
    df = df.copy()

    # get percentages
    df['procent_26'] = round(df['stemmer'] / df['total_gyldige_stemmer'] * 100 ,1)
    # find the parti_bogstav that corresponds with the biggest number of votes for each afstemningsområde
    df_stoerste_parti = (df.groupby([geo_id, geo_niveau, "parti_bogstav"])
        .agg({"stemmer": "sum"})
        .reset_index()
        .sort_values(by=[geo_niveau, "stemmer"], ascending=[True, False])
        .groupby(geo_niveau)
        .first()
        .reset_index()
    )
    
    # standardize party labels
    df_stoerste_parti = standardize_party_labels(df_stoerste_parti)

    # only keep geo_id, geo_niveau, parti_bogstav and parti but rename bogstav to "største_parti"
    df_stoerste_parti = df_stoerste_parti[[geo_id, geo_niveau, "bogstav", "parti"]]
    df_stoerste_parti = df_stoerste_parti.rename(columns={"bogstav": "biggest_party"})

     #calculage the percentage of votes each party got in each afstemningsområde and turn each party into a column
    party_votes = df.pivot(index=[geo_id, geo_niveau], columns="parti_bogstav", values="procent_26").fillna(0)
    party_votes = party_votes.reset_index()
    party_votes = party_votes.drop(columns=[col for col in party_votes.columns if str(col).strip() == "" or str(col).lower() == "nan"], errors="ignore")
    # change column names to the correct party letters based on the config file
    col_names = {
        "A": "S",
        "B": "R",
        "C": "K",
        "D": "NB",
        "F": "SF",
        "I": "LA",
        "K": "KD",
        "O": "DF",
        "Æ": "DD",
        "Ø": "EL",
        "Å": "ALT"
    }
    #rename the columns based on the col_names dictionary, if the column name is not in the dictionary, keep the original name
    party_votes = party_votes.rename(columns={col: col_names.get(col, col) for col in party_votes.columns})

    # join the percentage of votes for each party with the biggest party dataframe
    df_stoerste_parti = df_stoerste_parti.merge(party_votes, on=[geo_id, geo_niveau], how="left")

    # save dagi_id as a string to avoid issues with leading zeros
    df_stoerste_parti[geo_id] = df_stoerste_parti[geo_id].astype(str)

    return df_stoerste_parti

def udregn_personlige_stemmetal(df: pd.DataFrame, valgte_kandidater: pd.DataFrame) -> pd.DataFrame:
    # sum each candidate's votes at the specified geographic level (opstillingskreds, storkreds, nationalt)
    df_personlige_stemmer = (df.groupby(["kandidat_id","kandidat", "parti",'storkreds'])
        .agg({"stemmer": "sum"})
        .reset_index()
        .sort_values(by=["stemmer"], ascending=[False])
        .reset_index(drop=True)
    )

    # search for each candidate_id in the valgte_kandidater dataframe and add a column "valgt" with the value "√ valgt" if the candidate_id is in the valgte_kandidater dataframe, otherwise ""
    df_personlige_stemmer["valgt"] = df_personlige_stemmer["kandidat_id"].apply(lambda x: "√ valgt" if x in valgte_kandidater["kandidat_id"].values else "")
    #reorder columns to kandidat_id, kandidat, parti, storkreds, stemmer, valgt
    df_personlige_stemmer = df_personlige_stemmer[["kandidat_id", "kandidat", "parti", "storkreds", "valgt", "stemmer"]]

    return df_personlige_stemmer

# ----------------------------
# Kald funktionerne for hver opstillingskreds, storkreds og nationalt
# ----------------------------

if __name__ == "__main__":
    
    # -----------------------------
    # Process hver opstillingskreds
    for opstillingskreds in resultater_partier["opstillingskreds"].unique():
        df_opstillingskreds = resultater_partier[resultater_partier["opstillingskreds"] == opstillingskreds]
        opstillingskreds_id = df_opstillingskreds["opstillingskreds_dagi_id"].iloc[0]
        df_2022_opstillingskreds = resultater_opstillingskredse_2022[resultater_opstillingskredse_2022["opstillingskreds_dagi"] == opstillingskreds_id]
        # get status for the opstillingskreds
        status = udregn_status(df_opstillingskreds)
        status.to_csv(f"data/struktureret/opstillingskredse/status/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}_status.csv", index=False)
        try:
            res = udregn_procenter(df_opstillingskreds, df_2022_opstillingskreds)
            
            #turn into a dataframe and save as csv
            res_df = pd.DataFrame(res)
            res_df.to_csv(f"data/struktureret/opstillingskredse/procenter/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}.csv", index=False)
        except ValueError as e:
            print(f"Warning: {opstillingskreds} - {e}")

        stoerste_parti = udregn_stoerste_parti(df_opstillingskreds, "afstemningsområde", "afstemningsområde_dagi_id")
        stoerste_parti.to_csv(f"data/struktureret/opstillingskredse/kort/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}.csv", index=False)

    for opstillingskreds in resultater_kandidater["opstillingskreds"].unique():
        df_opstillingskreds = resultater_kandidater[resultater_kandidater["opstillingskreds"] == opstillingskreds]
        personlige_stemmer = udregn_personlige_stemmetal(df_opstillingskreds, valgte_kandidater)
        # drop opstillingskreds and kandidat_id columns to save space, since we already have kandidat and opstillingskreds in the filename
        personlige_stemmer = personlige_stemmer.drop(columns=["storkreds", "kandidat_id"])
        personlige_stemmer.to_csv(f"data/struktureret/opstillingskredse/personlige_stemmer/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}.csv", index=False)
    
    # ----------------------
    # Process hver storkreds
    for storkreds in resultater_partier["storkreds"].unique():
        df_storkreds = resultater_partier[resultater_partier["storkreds"] == storkreds]
        storkreds_id = df_storkreds["storkreds_nummer"].iloc[0]
        df_2022_storkreds = resultater_storkredse_2022[resultater_storkredse_2022["storkreds_dagi"] == storkreds_id]

        # få status på stemmeoptællingen for hver storkreds
        status = udregn_status(df_storkreds)
        status.to_csv(f"data/struktureret/storkredse/status/{storkreds_id}_{danish_to_ascii_filename(storkreds)}_status.csv", index=False)

        try:
            res = udregn_procenter(df_storkreds, df_2022_storkreds)
            res_df = pd.DataFrame(res)
            res_df.to_csv(f"data/struktureret/storkredse/procenter/{storkreds_id}_{danish_to_ascii_filename(storkreds)}.csv", index=False)
        except ValueError as e:
            print(f"Warning: storkreds {storkreds} - {e}")

        stoerste_parti = udregn_stoerste_parti(df_storkreds, "afstemningsområde", "afstemningsområde_dagi_id")
        stoerste_parti.to_csv(f"data/struktureret/storkredse/kort/{storkreds_id}_{danish_to_ascii_filename(storkreds)}.csv", index=False)
    
    for storkreds in resultater_kandidater["storkreds"].unique():
        df_storkreds = resultater_kandidater[resultater_kandidater["storkreds"] == storkreds]
        personlige_stemmer = udregn_personlige_stemmetal(df_storkreds,valgte_kandidater)
        # drop storkreds and kandidat_id columns to save space, since we already have kandidat and storkreds in the filename
        personlige_stemmer = personlige_stemmer.drop(columns=["storkreds", "kandidat_id"])
        personlige_stemmer.to_csv(f"data/struktureret/storkredse/personlige_stemmer/{storkreds_id}_{danish_to_ascii_filename(storkreds)}.csv", index=False)

    # -----------------
    # Process nationalt

    # få status på stemmeoptællingen for nationalt
    status = udregn_status(resultater_partier)
    status.to_csv(f"data/struktureret/nationalt/status/nationalt_status.csv", index=False)

    # Udregn hvor mange procent af stemmerne, hvert parti har fået på landsplan
    try:
        res = udregn_procenter(resultater_partier, resultater_nationalt_2022)
        res_df = pd.DataFrame(res)
        res_df.to_csv(f"data/struktureret/nationalt/procenter/nationalt_procenter.csv", index=False)
    except ValueError as e:
        print(f"Warning: national results - {e}")

    # get personlige stemmetal
    personlige_stemmer = udregn_personlige_stemmetal(resultater_kandidater, valgte_kandidater)
    personlige_stemmer.to_csv(f"data/struktureret/nationalt/personlige_stemmer/personlige_stemmer.csv", index=False)



    
