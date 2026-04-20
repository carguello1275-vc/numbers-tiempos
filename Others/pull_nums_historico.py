import cloudscraper
import pandas as pd
from datetime import date

#df = data frame
scraper = cloudscraper.create_scraper()
url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"
Fecha_inicial = "2026-01-01"    #"2020-01-01" "2020-05-01" "2020-09-01" 
Fecha_final = "2026-04-30"      #"2020-04-30" "2020-08-31" "2020-12-31" 
save_folder = "D:/777/numbers-tiempos/"

params = {
    "fechaInicio": Fecha_inicial ,
    "fechaFin": Fecha_final
}

headers = {
    "Authorization": "sec_num",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://integration.jps.go.cr/",
    "Origin": "https://integration.jps.go.cr",
    "Connection": "keep-alive"
}

response = scraper.get(url, params=params, headers=headers)

data = response.json()

# la parte para darle formato
rows = []

for day in data:
    if not isinstance(day, dict):
        continue

    dia = day.get("dia")

    try:
        dia = pd.to_datetime(dia, errors="coerce")
        dia = dia.strftime("%d/%m/%Y") if pd.notnull(dia) else ""
    except:
        dia = ""

    for periodo in ["manana", "mediaTarde", "tarde"]:
        draw = day.get(periodo)

        if isinstance(draw, dict):
            rows.append({
                "dia": dia,
                "numero": draw.get("numero"),
            })

df = pd.DataFrame(rows)

df.to_csv(f"{save_folder}Numeros_favorecidos{Fecha_inicial} a {Fecha_final}.csv", index=False)
