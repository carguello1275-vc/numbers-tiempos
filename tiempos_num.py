from flask import Flask, jsonify
import cloudscraper
import pandas as pd
from datetime import date

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "API is running"

@app.route("/run", methods=["GET"])
def run_script():
    try:
        # Setup
        scraper = cloudscraper.create_scraper()
        url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"
        today = date.today().strftime("%Y-%m-%d")

        params = {
            "fechaInicio": "2026-01-01",
            "fechaFin": today
        }

        headers = {
            "Authorization": "sec_num",  # <-- replace with real token
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://integration.jps.go.cr/",
            "Origin": "https://integration.jps.go.cr",
            "Connection": "keep-alive"
        }

        # Request
        response = scraper.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Transform data
        rows = []

        for day in data:
            dia = day.get("dia")

            for periodo in ["manana", "mediaTarde", "tarde"]:
                draw = day.get(periodo)

                if draw:
                    rows.append({
                        "dia": dia,
                        "numero": draw.get("numero")
                    })

        # DataFrame
        df = pd.DataFrame(rows)

        if df.empty:
            return jsonify({
                "status": "error",
                "message": "No data retrieved"
            }), 400

        df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        # Save CSV (optional)
        df.to_csv("Numeros_favorecidos.csv", index=False)

        # Return JSON
        return jsonify({
            "status": "success",
            "rows": len(df),
            "data": df.to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
