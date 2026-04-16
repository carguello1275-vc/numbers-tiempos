from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
import traceback
import random

app = Flask(__name__)


@app.route("/")
def home():
    return "API is running"


@app.route("/run", methods=["GET"])
def run_script():
    try:
        today = date.today().strftime("%Y-%m-%d")

        api_url = f"https://integration.jps.go.cr/api/App/nuevostiempos/historical?fechaInicio=2026-01-01&fechaFin={today}"

        # 🔥 Sticky session (IMPORTANT)
        session_id = f"session-{random.randint(100000,999999)}"

        proxy_username = f"spi5uiwom8-country-CR-{session_id}"
        proxy_password = "CxWrg7Eayo+93J0nnd"

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": "http://gate.decodo.com:10001",
                    "username": proxy_username,
                    "password": proxy_password
                },
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )

            page = context.new_page()
            page.set_default_timeout(45000)

            # 🔥 Warm-up (helps proxy reliability)
            page.goto("https://www.google.com", timeout=30000)

            # 🔥 Main navigation (faster strategy)
            page.goto(
                "https://integration.jps.go.cr",
                timeout=60000,
                wait_until="domcontentloaded"
            )

            # Small delay to stabilize
            page.wait_for_timeout(3000)

            # 🔥 Detect Cloudflare block early
            if "Verificación" in page.title():
                return jsonify({
                    "status": "error",
                    "message": "Blocked by Cloudflare (challenge page)"
                }), 403

            # 🔥 Call API INSIDE browser (key step)
            data = page.evaluate(f"""
                async () => {{
                    const res = await fetch("{api_url}", {{
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

            browser.close()

        # 🔴 Handle API / Cloudflare errors
        if isinstance(data, dict) and data.get("error"):
            return jsonify({
                "status": "error",
                "http_status": data.get("status"),
                "response_preview": data.get("text")[:500]
            }), 500

        if not isinstance(data, list):
            return jsonify({
                "status": "error",
                "message": "Unexpected response format",
                "preview": str(data)[:500]
            }), 500

        # ✅ Process data
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
