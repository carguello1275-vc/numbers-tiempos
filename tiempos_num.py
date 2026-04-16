from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import pandas as pd
from datetime import date
import os
import traceback

app = Flask(__name__)


@app.route("/")
def home():
    return "API is running"


# 🔥 MAIN JOB (uses Playwright + proxy)
@app.route("/run", methods=["GET"])
def run_script():
    try:
        today = date.today().strftime("%Y-%m-%d")
        url = f"https://integration.jps.go.cr/api/App/nuevostiempos/historical?fechaInicio=2026-01-01&fechaFin={today}"

        # ✅ Proxy config from environment
        proxy_server = os.environ.get("PROXY_SERVER")
        proxy_username = os.environ.get("PROXY_USERNAME")
        proxy_password = os.environ.get("PROXY_PASSWORD")

        if not proxy_server:
            return jsonify({
                "status": "error",
                "message": "Proxy not configured"
            }), 500

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": proxy_server,
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
                locale="en-US",
                timezone_id="America/Costa_Rica",
                viewport={"width": 1920, "height": 1080}
            )

            page = context.new_page()

            # ✅ Apply stealth
            stealth_sync(page)

            page.set_default_timeout(15000)

            # Step 1: Load site (pass Cloudflare)
            page.goto("https://integration.jps.go.cr", timeout=30000)

            try:
                page.wait_for_function(
                    "() => !document.title.includes('Verificación')",
                    timeout=10000
                )
            except:
                pass

            # Minimal human behavior
            page.mouse.move(100, 100)
            page.mouse.move(500, 400)
            page.wait_for_timeout(1500)

            # Fail fast if blocked
            if "Verificación" in page.title():
                return jsonify({
                    "status": "error",
                    "message": "Blocked by Cloudflare (proxy likely low quality)"
                }), 403

            # Step 2: Call API
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

        # Handle API errors
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

        # 🔥 Transform data (your original logic)
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

        # ✅ Save CSV (cache)
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


# 🔥 FAST ENDPOINT (no Playwright)
@app.route("/data", methods=["GET"])
def get_data():
    try:
        if not os.path.exists("Numeros_favorecidos.csv"):
            return jsonify({
                "status": "error",
                "message": "No cached data available"
            }), 500

        df = pd.read_csv("Numeros_favorecidos.csv")

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
