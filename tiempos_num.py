from flask import Flask, Response, jsonify
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
import io

app = Flask(__name__)


def fetch_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        context = browser.new_context()
        page = context.new_page()

        # Load site first (important for cookies/session)
        page.goto("https://integration.jps.go.cr/", timeout=60000)

        # Call API using browser session
        response = page.request.get(
            "https://integration.jps.go.cr/api/App/nuevostiempos/historical",
            params={
                "fechaInicio": "2026-01-01",
                "fechaFin": date.today().strftime("%Y-%m-%d")
            }
        )

        data = response.json()
        browser.close()
        return data


@app.route("/")
def home():
    return "API is running"


@app.route("/run", methods=["GET"])
def run_script_numbers():
    try:
        data = fetch_data()

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
