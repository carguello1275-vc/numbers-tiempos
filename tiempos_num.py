from flask import Flask, jsonify, Response
import cloudscraper
import pandas as pd
from datetime import date
import io
import time

app = Flask(__name__)

@app.route("/run", methods=["GET", "POST"])
def fetch_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://integration.jps.go.cr/", timeout=60000)

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
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": str(type(e))
        }), 500
