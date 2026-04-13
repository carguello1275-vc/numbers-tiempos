import cloudscraper
import pandas as pd
from datetime import date
from flask import Flask, jsonify
import requests


app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "API is running"


@app.route("/run", methods=["GET","POST"])
def run_script_numbers():

    def run_script_check():
        try:
            scraper = cloudscraper.create_scraper()
            url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"
            today = date.today()

            params = {
                   "fechaInicio": "2026-01-01",
                  "fechaFin": today
                    }

            headers = {
                    "Authorization": "sec_num"
                    }

            response = scraper.get(url, params=params, headers=headers)

            data = response.json()


            rows = []

            for day in data:
            dia = day.get("dia")

            for periodo in ["manana", "mediaTarde", "tarde"]:
            draw = day.get(periodo)

            if draw:
                rows.append({
                    "dia": dia,
                    #"periodo": periodo,
                    "numero": draw.get("numero"),
                    #"meganNumero": draw.get("meganNumero??"),
                    #"premio": draw.get("premio"),
                    #"reventado": draw.get("in_reventado"),
                    #"numeroSorteo": draw.get("numeroSorteo"),
                    #"fecha_sorteo": draw.get("fecha"),
                    #"porcentaje": draw.get("porcentaje"),
                    #"color": draw.get("colorBolita")
                })

            df = pd.DataFrame(rows)

            df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_data = output.getvalue()

            return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=Numeros_favorecidos.csv"
            })

        except Exception as e:
            return jsonify({
               "error": str(e),
                "type": str(type(e))
            })
