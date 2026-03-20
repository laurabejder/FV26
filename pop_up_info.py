import pandas as pd

largest_party_colors = {
    "Socialdemokratiet": "#F00B2F",
    "Venstre": "#0781DD",
    "Dansk Folkeparti": "#F6BA00",
    "Enhedslisten": "#FF7400",
    "Liberal Alliance": "#48CEF3",
    "SF": "#F257A9",
    "Radikale": "#662690",
    "Konservative": "#06691E",
    "Alternativet": "#3CE63D",
    "Kristendemokraterne": "#8B8474",
    "Nye Borgerlige": "#004E62",
    "Moderaterne": "#911995",
    "Frie Grønne": "#eecbc6",
    "Danmarksdemokraterne": "#0075c9",
}

party_colors = {
    "S":  "#F00B2F",
    "V":  "#0781DD",
    "DF": "#F6BA00",
    "EL": "#FF7400",
    "LA": "#48CEF3",
    "SF": "#F257A9",
    "R":  "#662690",
    "K":  "#06691E",
    "ALT": "#3CE63D",
    "KD": "#8B8474",
    "NB": "#004E62",
    "M":  "#911995",
    "FG": "#eecbc6",
    "DD": "#0075c9",
}

default_color = "#494949"
party_columns = ['S', "R", "K", "SF", "BP", "LA", "M", "DF", "V", "DD", "EL", "ALT", "UP"]

def make_popup(row, geo, default_color, party_columns):
    largest = row["parti"]
    valg = row[geo]

    # if valg is afstemningsområde add på valgested before the name
    if geo == "afstemningsområde":
        valg = f"på valgstedet {valg}"
    elif geo == "storkreds":
        valg = f"i {valg}s Storkreds"
    else: 
        valg = f"i {valg}kredsen"

    header_color = largest_party_colors.get(largest, default_color)

    # Header line
    header = (
        f"<b style='color:{header_color}; font-size:1.5em;margin-bottom: 10px'>{largest}</b><br> "
        f"blev størst {valg}<br>"
    )

    rows = []
    for party in party_columns:
        pct = row.get(party, pd.NA)  # avoids KeyError if column is missing
        if pd.isna(pct):
            continue

        pct = float(pct)
        color = party_colors.get(party, default_color)

        # fixed-width label cell (so S: and SP: line up)
        label_span = (
            f"<span style='display:inline-block; width:30px; font-size:1em;"
            f"vertical-align:middle; margin-left: 4px'>{party}</span>"
        )

        # bar cell
        bar_span = (
            f"<span style='display:inline-block; "
            f"width:0.3em; height:1.2em; vertical-align:middle;"
            f"background:{color};'></span>"
        )

        # percentage cell, fixed width & right-aligned
        pct_span = (
            f"<span style='display:inline-block; width:50px; "
            f"text-align:left; font-size:1em; vertical-align:middle'>{pct:.1f}%</span>"
        )

        line = bar_span + label_span + pct_span
        rows.append((pct, line))

    # sort by percentage descending
    rows.sort(key=lambda x: x[0], reverse=True)

    body = "<br>".join(line for _, line in rows)
    return header + body


def generate_popups(df, geo):
    default_color = "#494949"
    party_columns = ['S', "R", "K", "SF", "BP", "LA", "M", "DF", "V", "DD", "EL", "ALT", "UP"]

    df["popup"] = df.apply(lambda row: make_popup(row, geo, default_color, party_columns), axis=1)
    return df

