from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "API is running"

@app.route("/run", methods=["GET"])
def run_script():
    try:
        today = date.today().strftime("%Y-%m-%d")
        url = f"https://integration.jps.go.cr/api/App/nuevostiempos/historical?fechaInicio=2026-01-01&fechaFin={today}"

        token = os.environ.get("API_TOKEN", "sec_num")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            page = context.new_page()

            # Step 1: Load main page (VERY IMPORTANT)
            page.goto("https://integration.jps.go.cr", timeout=60000)

            # Step 2: Wait a bit (Cloudflare behavior simulation)
            page.wait_for_timeout(3000)

            # Step 3: Call API from browser context
            data = page.evaluate(f"""
                async () => {{
                    const res = await fetch("{url}", {{
                        headers: {{
                            "Authorization": "{token}"
                        }}
                    }});
                    return await res.json();
                }}
            """)

            browser.close()

        # Process data
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
            return jsonify({"status": "error", "message": "No data"}), 400

        df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

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
