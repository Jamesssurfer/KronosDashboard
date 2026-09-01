import os
import urllib.request
import json
import time
from datetime import datetime

# Paste your free Alpha Vantage key here
API_KEY = os.environ.get('ALPHA_VANTAGE_KEY', '')  # Better to use environment variable

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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        .error-message {{ color: #f87171; font-size: 12px; margin-top: 5px; }}
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
    html_content += f'        <button class="tab-btn {active_class}" onclick="switchTab(\'tab-{index}\', this)">{ticker}</button>\n'
html_content += "    </div>\n"

# 3. Fetch data for each ticker
for index, ticker in enumerate(tickers):
    # Alpha Vantage free tier: 5 requests per minute, 500 per day
    # Add delay between requests (except first)
    if index > 0:
        print(f"Waiting 12 seconds before fetching {ticker}...")
        time.sleep(12)
    
    active_section = "active" if index == 0 else ""
    current_price = "Loading..."
    price_change_pct = 0.0
    direction_bias = "Neutral"
    bias_style = "neutral"
    historical_closes = []
    historical_dates = []
    error_message = ""
    
    if not API_KEY:
        error_message = "API key missing"
    else:
        # Build correct API URL based on asset type
        if ticker == "XAU-USD":
            # Gold spot price (using CURRENCY_EXCHANGE_RATE for XAU/USD)
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=USD&apikey={API_KEY}"
        elif "BTC" in ticker:
            # Cryptocurrency
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={ticker.split('-')[0]}&market=USD&apikey={API_KEY}"
        else:
            # Regular stocks
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            # Check for error messages
            if "Error Message" in data:
                error_message = data["Error Message"]
            elif "Note" in data:
                error_message = "API rate limit reached"
            elif "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                sorted_dates = sorted(time_series.keys())[-30:]  # Get last 30 days
                historical_closes = [float(time_series[d]["4. close"]) for d in sorted_dates]
                historical_dates = [d[5:] for d in sorted_dates]  # Format: MM-DD
            
            elif "Time Series (Digital Currency Daily)" in data:
                time_series = data["Time Series (Digital Currency Daily)"]
                sorted_dates = sorted(time_series.keys())[-30:]
                historical_closes = [float(time_series[d]["4a. close (USD)"]) for d in sorted_dates]
                historical_dates = [d[5:] for d in sorted_dates]
            
            elif "Realtime Currency Exchange Rate" in data:
                # For XAU/USD, we only get current rate, not historical
                exchange_data = data["Realtime Currency Exchange Rate"]
                current_rate = float(exchange_data["5. Exchange Rate"])
                historical_closes = [current_rate]  # Only current price available
                historical_dates = [datetime.now().strftime('%m-%d')]
                
        except Exception as e:
            error_message = f"Error: {str(e)}"
    
    # Calculate metrics if we have data
    if historical_closes and len(historical_closes) >= 2:
        current_price = f"${historical_closes[-1]:,.2f}"
        price_change_pct = ((historical_closes[-1] - historical_closes[-2]) / historical_closes[-2]) * 100
        
        # Calculate 20-day moving average for trend
        ma20 = sum(historical_closes[-20:]) / min(20, len(historical_closes))
        if historical_closes[-1] > ma20:
            direction_bias = "Bullish Trend"
            bias_style = "bullish"
        else:
            direction_bias = "Bearish Trend"
            bias_style = "bearish"
    else:
        # Fallback data
        historical_closes = [150, 152, 151, 153, 155, 154, 156, 158, 157, 160, 159, 161, 163, 162, 165, 167, 166, 168, 170, 169]
        historical_dates = ["08-10", "08-11", "08-12", "08-13", "08-14", "08-17", "08-18", "08-19", "08-20", "08-21", "08-22", "08-23", "08-24", "08-25", "08-26", "08-27", "08-28", "08-29", "08-30", "08-31"]
        current_price = "API Fetch Failed"
        if error_message:
            current_price = f"Error: {error_message[:20]}"
    
    # Build the HTML content for this ticker
    html_content += f"""
    <div id="tab-{index}" class="content-section {active_section}">
        <div class="grid-layout">
            <div class="panel">
                <div class="panel-title">{ticker} Data Statistics</div>
                <div class="metric-card">
                    <div class="metric-label">Last Tracked Close Price</div>
                    <div class="metric-value">{current_price}</div>
                    {f'<div class="error-message">{error_message}</div>' if error_message else ''}
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
                labels: {json.dumps(historical_dates)},
                datasets: [{{
                    label: '{ticker}',
                    data: {json.dumps(historical_closes)},
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

# Add the tab switching script
html_content += """
    <script>
        function switchTab(tabId, btnElement) {
            // Hide all sections
            var sections = document.getElementsByClassName('content-section');
            for (var i = 0; i < sections.length; i++) {
                sections[i].classList.remove('active');
            }
            
            // Remove active class from all buttons
            var buttons = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].classList.remove('active');
            }
            
            // Show selected section and activate button
            document.getElementById(tabId).classList.add('active');
            btnElement.classList.add('active');
        }
    </script>
</body>
</html>
"""

# Write the HTML file
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Dashboard generated successfully!")
