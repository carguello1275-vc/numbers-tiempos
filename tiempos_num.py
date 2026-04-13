import cloudscraper
import pandas as pd
from datetime import date
from flask import Flask, jsonify
import requests


app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "API is running"


@app.route("/run", methods=["GET", "POST"])
def run_script_numbers():
    try:
        scraper = cloudscraper.create_scraper()

        url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"

        params = {
            "fechaInicio": "2026-01-01",
            "fechaFin": date.today().strftime("%Y-%m-%d")
        }

        headers = {
            "Authorization": "sec_num"
        }

        response = scraper.get(url, params=params, headers=headers)

        if response.status_code != 200:
            return jsonify({
                "error": "API request failed",
                "status": response.status_code
            }), 500

        data = response.json()

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

        df = pd.DataFrame(rows)

        if df.empty:
            return jsonify({"message": "No data available"}), 200

        df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        output = io.StringIO()
        df.to_csv(output, index=False)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=Numeros_favorecidos.csv"
            }
        )

    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": str(type(e))
        }), 500
