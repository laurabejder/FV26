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

# Hent vores oversigt over, hvilke kandidater der er valgt ind i Folketinget
valgte_kandidater = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vTxLGlQjnEd-RGHCbVNhWzxmTH9dL6TiNlJHMbeVSwolMSEZN6uV4pc45iLLF0xUym26XwrFiXVhFFr/pub?gid=0&single=true&output=csv")

# Indlæs resultaterne fra sidste valg, så vi kan sammenligne og udregne forskelle
resultater_opstillingskredse_2022 = pd.read_csv("data/resultater_2022/processed/opstillingskreds_resultater.csv")
resultater_storkredse_2022 = pd.read_csv("data/resultater_2022/processed/storkreds_resultater.csv")
resultater_nationalt_2022 = pd.read_csv("data/resultater_2022/processed/nationalt_resultater.csv")

# ----------------------------
# Definer støttende funktioner
# ----------------------------

# Fjern ufærdige resultater
def resultater_findes(data):
    return data[data["resultat_art"] != 'IngenResultater']

# Konverter Dansk tegnsætning til ASCII for at standardisere filnavne
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

# Standardiser partinavne og -bogstaver
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

    total_gyldige_stemmer = df.groupby("afstemningsområde_dagi_id")["total_gyldige_stemmer"].first().sum() # Find det samlede antal gyldige stemmer for hele opstillingskredsen ved at tage det første (og samme) antal gyldige stemmer for hvert afstemningsområde og summere dem
    df = (df
        .groupby("parti")
        .agg({
            "stemmer": "sum",
            "total_gyldige_stemmer": lambda x: total_gyldige_stemmer
        })
        .reset_index()
        )

    df["procent_26"] = round((df["stemmer"] / df["total_gyldige_stemmer"]) * 100, 1) # Udregn procentfordelingen og afrund til et decimal

    # # Tjek om procenterne summerer til 100. Hvis ikke: skrig!
    # procent_sum = df["procent_26"].sum()
    # if procent_sum == 0:
    #     return df
    # elif not (99.9 <= procent_sum <= 100.1):
    #     raise ValueError(f"Procenterne summerer ikke til 100% (summerer til {procent_sum:.2f}%)")

    df["parti_bogstav"] = df["parti"].map({p["navn"]: p["bogstav"] for p in partier_info}).fillna(df["parti"]) # Standardiser partinavne og -bogstaver

    # Join med 2022-resultaterne for at kunne sammenligne og udregne forskelle i procenter mellem de to valg
    df = df.merge(
        resultater_2022[["Partibogstav", "procent_22"]],
        left_on="parti_bogstav",
        right_on="Partibogstav",
        how="left"
    ).drop(columns=["Partibogstav"])

    df = df[["parti_bogstav", "parti", "procent_26", "procent_22"]] # Ændr rækkefølgen af kolonner for bedre læsbarhed
    return df

def udregn_status(df: pd.DataFrame) -> pd.DataFrame:
    # Find antallet af valgsteder, der har en foreløbig optælling eller fintælling, for at kunne udregne status på optællingen
    foreløbig_optælling = df[df["resultat_art"].isin(["ForeløbigOptælling", "Fintælling"])]["afstemningsområde_dagi_id"].nunique()
    status_df = pd.DataFrame({
        "Optalte valgsteder": [foreløbig_optælling]
    })
    return status_df

def udregn_stoerste_parti(df: pd.DataFrame, geo_niveau, geo_id) -> pd.DataFrame:
    df = df.copy()

    # Udregn procentfordelingen for hvert parti i hvert afstemningsområde
    df['procent_26'] = round(df['stemmer'] / df['total_gyldige_stemmer'] * 100 ,1)
    # Find det parti, der har fået flest stemmer i hvert afstemningsområde/opstillingskreds/storkreds
    df_stoerste_parti = (df.groupby([geo_id, geo_niveau, "parti_bogstav"])
        .agg({"stemmer": "sum"})
        .reset_index()
        .sort_values(by=[geo_niveau, "stemmer"], ascending=[True, False])
        .groupby(geo_niveau)
        .first()
        .reset_index()
    )
    
    df_stoerste_parti = standardize_party_labels(df_stoerste_parti) # Standardiser partinavne og -bogstaver

    # Behold kun de nødvendige kolonner + omdøb for klarhed
    df_stoerste_parti = df_stoerste_parti[[geo_id, geo_niveau, "bogstav", "parti"]]
    df_stoerste_parti = df_stoerste_parti.rename(columns={"bogstav": "biggest_party"})

    # Udregn procentfordelingen for hvert parti i hvert afstemningsområde og omdann hvert parti til en kolonne
    party_votes = df.pivot(index=[geo_id, geo_niveau], columns="parti_bogstav", values="procent_26").fillna(0)
    party_votes = party_votes.reset_index()
    party_votes = party_votes.drop(columns=[col for col in party_votes.columns if str(col).strip() == "" or str(col).lower() == "nan"], errors="ignore")
    # Ændr kolonnenavne til de korrekte partibogstaver baseret på konfigurationsfilen
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
    # Omdøb kolonnerne baseret på col_names-ordbogen, hvis kolonnenavnet ikke findes i ordbogen, behold det oprindelige navn
    party_votes = party_votes.rename(columns={col: col_names.get(col, col) for col in party_votes.columns})

    # Join procentfordelingen for hvert parti med dataframe for det største parti
    df_stoerste_parti = df_stoerste_parti.merge(party_votes, on=[geo_id, geo_niveau], how="left")

    # Gem dagi_id som en string for at undgå problemer med foranstillede nuller
    df_stoerste_parti[geo_id] = df_stoerste_parti[geo_id].astype(str)

    return df_stoerste_parti

def udregn_personlige_stemmetal(df: pd.DataFrame, valgte_kandidater: pd.DataFrame, geo_niveau: str) -> pd.DataFrame:
    # Summer hver kandidats stemmer på det angivne geografiske niveau (opstillingskreds, storkreds, nationalt)
    df_personlige_stemmer = (df.groupby(["kandidat_id","kandidat", "parti", geo_niveau])
        .agg({"stemmer": "sum"})
        .reset_index()
        .sort_values(by=["stemmer"], ascending=[False])
        .reset_index(drop=True)
    )

    df_personlige_stemmer["valgt"] = df_personlige_stemmer["kandidat_id"].apply(lambda x: "✓" if x in valgte_kandidater["kandidat_id"].values else "")
    df_personlige_stemmer = df_personlige_stemmer[["kandidat_id", "kandidat", "parti", geo_niveau, "valgt", "stemmer"]]

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

        if df_opstillingskreds["resultat_art"].isin(["ForeløbigOptælling", "Fintælling"]).all():
            stoerste_parti = udregn_stoerste_parti(df_opstillingskreds, "afstemningsområde", "afstemningsområde_dagi_id")
            stoerste_parti.to_csv(f"data/struktureret/opstillingskredse/kort/{opstillingskreds_id}_{danish_to_ascii_filename(opstillingskreds)}.csv", index=False)

    for opstillingskreds in resultater_kandidater["opstillingskreds"].unique():
        df_opstillingskreds = resultater_kandidater[resultater_kandidater["opstillingskreds"] == opstillingskreds]
        opstillingskreds_id = df_opstillingskreds["opstillingskreds_dagi_id"].iloc[0]
        personlige_stemmer = udregn_personlige_stemmetal(df_opstillingskreds, valgte_kandidater, "opstillingskreds")
        personlige_stemmer = personlige_stemmer.drop(columns=["opstillingskreds", "kandidat_id"])
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

        if df_storkreds["resultat_art"].isin(["ForeløbigOptælling", "Fintælling"]).all():
            stoerste_parti = udregn_stoerste_parti(df_storkreds, "afstemningsområde", "afstemningsområde_dagi_id")
            stoerste_parti.to_csv(f"data/struktureret/storkredse/kort/{storkreds_id}_{danish_to_ascii_filename(storkreds)}.csv", index=False)
    
    for storkreds in resultater_kandidater["storkreds"].unique():
        df_storkreds = resultater_kandidater[resultater_kandidater["storkreds"] == storkreds]
        storkreds_id = df_storkreds["storkreds_nummer"].iloc[0]
        personlige_stemmer = udregn_personlige_stemmetal(df_storkreds,valgte_kandidater, "storkreds")
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
    personlige_stemmer = udregn_personlige_stemmetal(resultater_kandidater, valgte_kandidater, "storkreds")
    personlige_stemmer.to_csv(f"data/struktureret/nationalt/personlige_stemmer/personlige_stemmer.csv", index=False)


    def nationalt_stoerste_parti(resultater_partier, geo_id, geo) -> pd.DataFrame:
        # find storkredse hvor alle afstemningsområder har foreløbig optælling eller fintælling
        optalte_kredse = resultater_partier.groupby(geo_id)["resultat_art"].apply(lambda x: x.isin(["ForeløbigOptælling", "Fintælling"]).all())

        # standardize party names
        resultater_partier = standardize_party_labels(resultater_partier)
        bogstav_map = {p["listebogstav"]: p["bogstav"] for p in partier_info}
        totals = resultater_partier.groupby(geo_id)["stemmer"].sum()

        # aggregate, add bogstav, compute %, find biggest party per kommune, pivot wide
        nat_resultater = (
            resultater_partier
            .assign(bogstav=lambda d: d["parti_bogstav"].map(bogstav_map).fillna(d["parti_bogstav"]))
            .groupby([geo_id, geo, "parti", "bogstav"], as_index=False)["stemmer"].sum()
            .assign(
                storkreds_gyldige_stemmer=lambda d: d[geo_id].map(totals),
                procent_26=lambda d: d["stemmer"] / d["storkreds_gyldige_stemmer"] * 100,
            )
        )

        største = (
            nat_resultater
            .sort_values([geo, "procent_26"], ascending=[True, False])
            .drop_duplicates(geo)[[geo, "parti"]]
            .rename(columns={"parti": "største_parti"})
        )

        nat_resultater = (
            nat_resultater
            .merge(største, on=geo, how="left")
            .pivot_table(
                index=[geo_id, geo, "største_parti"],
                columns="bogstav",
                values="procent_26",
                aggfunc="max",   # or "mean" / "max" etc.
            )
            .reset_index()
        )
        # filter nat_resultater to the storkredse in optalte_storkredse
        nat_resultater = nat_resultater[nat_resultater[geo].isin(optalte_kredse.index[optalte_kredse])]

        # rename største parti column to parti
        nat_resultater = nat_resultater.rename(columns={"største_parti": "parti"})


        return nat_resultater
    
    storkredse_stoerste_parti = nationalt_stoerste_parti(resultater_partier, "storkreds_nummer", "storkreds")
    storkredse_stoerste_parti.to_csv(f"data/struktureret/nationalt/kort/storkredse_stoerste_parti.csv", index=False)
    opstillingskredse_stoerste_parti = nationalt_stoerste_parti(resultater_partier, "opstillingskreds_dagi_id", "opstillingskreds")
    opstillingskredse_stoerste_parti.to_csv(f"data/struktureret/nationalt/kort/opstillingskredse_stoerste_parti.csv", index=False)



    
