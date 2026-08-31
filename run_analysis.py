import os
import urllib.request
import json
import time  # Imported to handle the rate-limit delay
from datetime import datetime

# Paste your free Alpha Vantage key here
API_KEY = "UMZBMW136NPEAP1B"

# 1. Read tickers from your asset list
try:
    with open("tracked_assets.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    tickers = ["AAPL", "NVDA", "BTC-USD", "SPY", "XAU-USD"]

# 2. Build Dashboard Layout Header
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kronos Analysis Dashboard</title>
    <script src="https://jsdelivr.net"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 25px; margin: 0; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ font-size: 22px; color: #ffffff; margin: 0; font-weight: 600; }}
        .meta-info {{ font-size: 12px; color: #94a3b8; text-align: right; }}
        .tabs-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 25px; }}
        .tab-btn {{ background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 8px 16px; font-family: inherit; font-size: 13px; cursor: pointer; border-radius: 6px; transition: all 0.2s; }}
        .tab-btn:hover {{ background-color: #334155; color: #f8fafc; }}
        .tab-btn.active {{ background-color: #2563eb; color: #ffffff; border-color: #3b82f6; font-weight: 600; }}
        .grid-layout {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
        .panel {{ background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }}
        .panel-title {{ font-size: 14px; font-weight: 600; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }}
        .metric-card {{ background-color: #1f2937; border-radius: 6px; padding: 15px; margin-bottom: 15px; border-left: 4px solid #3b82f6; }}
        .metric-label {{ font-size: 12px; color: #94a3b8; margin-bottom: 4px; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #ffffff; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block; margin-top: 5px; }}
        .bullish {{ background-color: #10b98120; color: #34d399; border: 1px solid #34d39940; }}
        .bearish {{ background-color: #ef444420; color: #f87171; border: 1px solid #f8717140; }}
        .neutral {{ background-color: #64748b20; color: #94a3b8; border: 1px solid #94a3b840; }}
        .chart-container {{ position: relative; width: 100%; height: 320px; }}
        .content-section {{ display: none; }}
        .content-section.active {{ display: block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Kronos Analysis Dashboard</h1>
        <div class="meta-info">Data Matrix Active<br>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    </div>
    <div class="tabs-container">
"""

for index, ticker in enumerate(tickers):
    active_class = "active" if index == 0 else ""
    html_content += f'        <button class="tab-btn {active_class}" onclick="switchTab(\'tab-{index}\')">{ticker}</button>\n'
html_content += "    </div>\n"

# 3. Pull data structures cleanly using official API functions
for index, ticker in enumerate(tickers):
    # Add a 12-second sleep delay before every request EXCEPT the first one.
    # This paces the 5 assets across 60 seconds to satisfy the 5 requests/min rule.
    if index > 0:
        print(f"Pacing API requests. Waiting 12 seconds before fetching {ticker}...")
        time.sleep(12)

    active_section = "active" if index == 0 else ""
    current_price, price_change_pct, direction_bias, bias_style = "Loading...", 0.0, "Neutral", "neutral"
    historical_closes, historical_dates = [], []
    
    if ticker == "XAU-USD":
        url = f"https://alphavantage.co{API_KEY}"
    elif "BTC" in ticker:
        url = f"https://alphavantage.co{API_KEY}"
    else:
        url = f"https://alphavantage.co{ticker}&apikey={API_KEY}"
        
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            sorted_dates = sorted(time_series.keys())[-20:]
            historical_closes = [float(time_series[d]["4. close"]) for d in sorted_dates]
            historical_dates = [d[5:] for d in sorted_dates]
            
        elif "Time Series (Digital Currency Daily)" in data:
            time_series = data["Time Series (Digital Currency Daily)"]
            sorted_dates = sorted(time_series.keys())[-20:]
            historical_closes = [float(time_series[d]["4a. close (USD)"]) for d in sorted_dates]
            historical_dates = [d[5:] for d in sorted_dates]
            
        elif "data" in data:
            gold_data = data["data"][:20]
            gold_data.reverse()
            historical_closes = [float(item["value"]) for item in gold_data if item["value"] != "."]
            historical_dates = [item["date"][5:] for item in gold_data if item["value"] != "."]

        if historical_closes:
            current_price = f"${historical_closes[-1]:,.2f}"
            price_change_pct = ((historical_closes[-1] - historical_closes[-2]) / historical_closes[-2]) * 100
            
            if historical_closes[-1] > (sum(historical_closes) / len(historical_closes)):
                direction_bias, bias_style = "Bullish Trend", "bullish"
            else:
                direction_bias, bias_style = "Bearish Trend", "bearish"
                
    except Exception:
        pass

    if not historical_closes:
        historical_closes = [150, 152, 151, 153, 155, 154, 156, 158, 157, 160, 159, 161, 163, 162, 165, 167, 166, 168, 170, 169]
        historical_dates = ["08-10", "08-11", "08-12", "08-13", "08-14", "08-17", "08-18", "08-19", "08-20", "08-21", "08-22", "08-23", "08-24", "08-25", "08-26", "08-27", "08-28", "08-29", "08-30", "08-31"]
        current_price = "API Fetch Limit"

    html_content += f"""
    <div id="tab-{index}" class="content-section {active_section}">
        <div class="grid-layout">
            <div class="panel">
                <div class="panel-title">{ticker} Data Statistics</div>
                <div class="metric-card">
                    <div class="metric-label">Last Tracked Close Price</div>
                    <div class="metric-value">{current_price}</div>
                </div>
                <div class="metric-card" style="border-left-color: {'#34d399' if price_change_pct >= 0 else '#f87171'};">
                    <div class="metric-label">Daily Price Move</div>
                    <div class="metric-value" style="color: {'#34d399' if price_change_pct >= 0 else '#f87171'};">{price_change_pct:+.2f}%</div>
                </div>
                <div class="metric-card" style="border-left-color: {'#34d399' if bias_style == 'bullish' else '#f87171' if bias_style == 'bearish' else '#94a3b8'};">
                    <div class="metric-label">Calculated Directional Bias</div>
                    <span class="badge {bias_style}">{direction_bias}</span>
                </div>
            </div>
            <div class="panel">
                <div class="panel-title">{ticker} Historical Price Matrix</div>
                <div class="chart-container"><canvas id="chart-{index}"></canvas></div>
            </div>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('chart-{index}'), {{
            type: 'line',
            data: {{
                labels: {str(historical_dates)},
                datasets: [{{
                    data: {str(historical_closes)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.05)',
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: '#1e293b' }}, ticks: {{ color: '#94a3b8' }} }},
                    y: {{ grid: {{ color: '#1e293b' }}, ticks: {{ color: '#94a3b8' }} }}
                }}
            }}
        }});
    </script>
    """

html_content += """
    <script>
        function switchTab(tabId) {
            var sections = document.getElementsByClassName('content-section');
            for (var i = 0; i < sections.length; i++) { sections[i].classList.remove('active'); }
            var buttons = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < buttons.length; i++) { buttons[i].classList.remove('active'); }
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
