#!/usr/bin/env bash

pip install -r requirements.txt

# Install Playwright browsers WITHOUT root
playwright install chromium
