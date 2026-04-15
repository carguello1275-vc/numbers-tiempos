from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
import os
import traceback
import json

app = Flask(__name__)


@app.route("/")
def home():
    return "API is running"


@app.route("/run", methods=["GET"])
def run_script():
    try:
        today = date.today().strftime("%Y-%m-%d")
        url = f"https://integration.jps.go.cr/api/App/nuevostiempos/historical?fechaInicio=2026-01-01&fechaFin={today}"

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
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                viewport={"width": 1920, "height": 1080}
            )

            page = context.new_page()

            # ⬇️ IMPORTANT: reduce total timeout
            page.set_default_timeout(15000)

            # Step 1: Load site
            page.goto("https://integration.jps.go.cr", timeout=30000)

            # ⬇️ Wait briefly (NOT long)
            try:
                page.wait_for_function(
                    "() => !document.title.includes('Verificación')",
                    timeout=8000
                )
            except:
                pass  # don't block execution

            # ⬇️ Simulate minimal human behavior
            page.mouse.move(100, 100)
            page.mouse.move(400, 300)
            page.wait_for_timeout(1000)

            # ⬇️ Early exit if still blocked
            title = page.title()
            if "Verificación" in title:
                return jsonify({
                    "status": "error",
                    "message": "Blocked by Cloudflare (challenge not passed fast enough)"
                }), 403

            # Step 2: Call API safely
            data = page.evaluate(f"""
                async () => {{
                    const res = await fetch("{url}", {{
                        method: "GET",
                        headers: {{
                            "Authorization": "sec_num",
                            "Accept": "application/json, text/plain, */*"
                        }}
                    }});

                    const text = await res.text();

                    try {{
                        return JSON.parse(text);
                    }} catch (e) {{
                        return {{
                            error: true,
                            status: res.status,
                            text: text
                        }};
                    }}
                }}
            """)

        # Handle Cloudflare/API errors
        if isinstance(data, dict) and data.get("error"):
            return jsonify({
                "status": "error",
                "http_status": data.get("status"),
                "response_preview": data.get("text")[:500]
            }), 500

        # Validate response
        if not isinstance(data, list):
            return jsonify({
                "status": "error",
                "message": "Unexpected response format",
                "type": str(type(data)),
                "preview": str(data)[:500]
            }), 500

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
            return jsonify({
                "status": "error",
                "message": "No data retrieved"
            }), 400

        if "dia" in df.columns:
            df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%d/%m/%Y")

        df.to_csv("Numeros_favorecidos.csv", index=False)

        return jsonify({
            "status": "success",
            "rows": len(df),
            "data": df.to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
