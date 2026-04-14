from flask import Flask, jsonify
import requests
import pandas as pd
from datetime import date
import os
import time

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "API is running"

@app.route("/run", methods=["GET"])
def run_script():
    try:
        # Setup
        url = "https://integration.jps.go.cr/api/App/nuevostiempos/historical"
        today = date.today().strftime("%Y-%m-%d")

        params = {
            "fechaInicio": "2026-01-01",
            "fechaFin": today
        }

        # Use environment variable for token (IMPORTANT)
        token = os.environ.get("API_TOKEN", "sec_num")

        # Start session
        session = requests.Session()

        # Step 1: Visit main site (establish cookies/session)
        initial_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        session.get("https://integration.jps.go.cr", headers=initial_headers)

        # Optional: small delay to mimic real user behavior
        time.sleep(2)

        # Step 2: API request headers
        headers = {
            "Authorization": token,
            "User-Agent": initial_headers["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://integration.jps.go.cr/",
            "Origin": "https://integration.jps.go.cr",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive"
        }

        # Step 3: Call API using SAME session
        response = session.get(url, params=params, headers=headers)

        # Debug (optional – remove later)
        print("Status Code:", response.status_code)
        print("Cookies:", session.cookies.get_dict())

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

        df = pd.DataFrame(rows)

        if df.empty:
            return jsonify({
                "status": "error",
                "message": "No data retrieved"
            }), 400

        # Format date
        df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        # Save CSV (optional)
        df.to_csv("Numeros_favorecidos.csv", index=False)

        # Return JSON
        return jsonify({
            "status": "success",
            "rows": len(df),
            "data": df.to_dict(orient="records")
        })

    except requests.exceptions.HTTPError as http_err:
        return jsonify({
            "status": "error",
            "message": f"HTTP error: {str(http_err)}",
            "status_code": response.status_code if 'response' in locals() else None
        }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
