import cloudscraper
import pandas as pd
import subprocess
from datetime import date, timedelta

df_existing = pd.read_csv("Numeros_favorecidos.csv")
save_folder = "D:/777/numbers-tiempos/"

scraper = cloudscraper.create_scraper()
url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"
today = date.today()
yesterday = date.today() - timedelta(days=1)

params = {
    "fechaInicio": yesterday,
    "fechaFin": today
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
    dia = day.get("dia")

    for periodo in ["manana", "mediaTarde", "tarde"]:
        draw = day.get(periodo)

        if draw:
            rows.append({
                "dia": dia,
                "numero": draw.get("numero"),
            })

df = pd.DataFrame(rows)

df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")



df.to_csv(f"{save_folder}Numeros_favorecidos.csv", index=False)


try:
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "auto update csv"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Pushed to GitHub successfully")
except subprocess.CalledProcessError as e:
    print("Git command failed:", e)

    