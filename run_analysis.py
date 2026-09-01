import os
import urllib.request
import json
import time
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# Alpha Vantage API Key
API_KEY = os.environ.get('ALPHA_VANTAGE_KEY', 'UMZBMW136NPEAP1B')

# 1. Read tickers from your asset list
try:
    with open("tracked_assets.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    tickers = ["AAPL", "NVDA", "BTC-USD", "SPY", "XAU-USD", "DXY","US Oil"]

# Define which assets to fetch from MT5 vs Alpha Vantage
MT5_SYMBOLS = {
    "XAU-USD": "XAUUSD",
    "BTC-USD": "BTCUSD",
    "DXY": "USDIndex",  # Dollar Index (might need specific broker support)
    "US Oil": "USOIL.S",
}

# 2. Initialize MT5 (if any MT5 symbols exist)
mt5_initialized = False
if any(ticker in MT5_SYMBOLS for ticker in tickers):
    if not mt5.initialize():
        print("MT5 initialization failed")
        mt5_initialized = False
    else:
        mt5_initialized = True
        print("MT5 initialized successfully")

# 3. Build Dashboard Layout Header
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
        .data-source {{ font-size: 10px; color: #64748b; margin-top: 3px; }}
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

# 4. Function to fetch MT5 data
def fetch_mt5_data(symbol, timeframe=mt5.TIMEFRAME_D1, bars=30):
    """Fetch historical data from MT5"""
    if not mt5_initialized:
        return [], [], "MT5 not initialized"
    
    try:
        # Get historical data
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        
        if rates is None or len(rates) == 0:
            return [], [], f"No MT5 data for {symbol}"
        
        # Extract close prices and dates
        closes = [float(rate[4]) for rate in rates]  # Close price is index 4
        dates = [datetime.fromtimestamp(rate[0]).strftime('%m-%d') for rate in rates]  # Time is index 0
        
        return closes, dates, ""
        
    except Exception as e:
        return [], [], f"MT5 Error: {str(e)}"

# 5. Function to fetch Alpha Vantage data
def fetch_alpha_vantage_data(ticker):
    """Fetch data from Alpha Vantage"""
    if not API_KEY:
        return [], [], "API key missing"
    
    # Build URL based on asset type
    if "BTC" in ticker:
        crypto_symbol = ticker.split('-')[0]
        url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={crypto_symbol}&market=USD&apikey={API_KEY}"
    else:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            sorted_dates = sorted(time_series.keys())[-30:]
            closes = [float(time_series[d]["4. close"]) for d in sorted_dates]
            dates = [d[5:] for d in sorted_dates]
            return closes, dates, ""
        
        elif "Time Series (Digital Currency Daily)" in data:
            time_series = data["Time Series (Digital Currency Daily)"]
            sorted_dates = sorted(time_series.keys())[-30:]
            closes = [float(time_series[d]["4a. close (USD)"]) for d in sorted_dates]
            dates = [d[5:] for d in sorted_dates]
            return closes, dates, ""
        
        elif "Error Message" in data:
            return [], [], data["Error Message"]
        elif "Note" in data:
            return [], [], "Rate limit reached"
        else:
            return [], [], f"Unexpected format: {list(data.keys())[:3]}"
            
    except Exception as e:
        return [], [], f"Error: {str(e)}"

# 6. Fetch data for each ticker
for index, ticker in enumerate(tickers):
    active_section = "active" if index == 0 else ""
    current_price = "Loading..."
    price_change_pct = 0.0
    direction_bias = "Neutral"
    bias_style = "neutral"
    historical_closes = []
    historical_dates = []
    error_message = ""
    data_source = ""
    
    # Determine data source
    if ticker in MT5_SYMBOLS:
        # Fetch from MT5
        mt5_symbol = MT5_SYMBOLS[ticker]
        print(f"Fetching {ticker} from MT5 (symbol: {mt5_symbol})...")
        historical_closes, historical_dates, error_message = fetch_mt5_data(mt5_symbol)
        data_source = "MT5"
        
        # If MT5 fails for BTC, try Alpha Vantage as fallback
        if not historical_closes and "BTC" in ticker and API_KEY:
            print(f"MT5 failed for {ticker}, trying Alpha Vantage...")
            historical_closes, historical_dates, error_message = fetch_alpha_vantage_data(ticker)
            data_source = "Alpha Vantage"
    else:
        # Fetch from Alpha Vantage
        print(f"Fetching {ticker} from Alpha Vantage...")
        
        # Add delay for Alpha Vantage rate limiting
        if index > 0:
            # Count how many Alpha Vantage calls we've made
            av_calls = sum(1 for t in tickers[:index] if t not in MT5_SYMBOLS)
            if av_calls > 0:
                print(f"Waiting 12 seconds for Alpha Vantage rate limit...")
                time.sleep(12)
        
        historical_closes, historical_dates, error_message = fetch_alpha_vantage_data(ticker)
        data_source = "Alpha Vantage"
    
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
        historical_closes = [150, 152, 151, 153, 155, 154, 156, 158, 157, 160]
        historical_dates = ["08-10", "08-11", "08-12", "08-13", "08-14", "08-17", "08-18", "08-19", "08-20", "08-21"]
        current_price = "Fetch Failed"
    
    # Build HTML for this ticker
    html_content += f"""
    <div id="tab-{index}" class="content-section {active_section}">
        <div class="grid-layout">
            <div class="panel">
                <div class="panel-title">{ticker} Data Statistics</div>
                <div class="metric-card">
                    <div class="metric-label">Last Tracked Close Price</div>
                    <div class="metric-value">{current_price}</div>
                    <div class="data-source">Source: {data_source}</div>
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

# Add tab switching script
html_content += """
    <script>
        function switchTab(tabId, btnElement) {
            var sections = document.getElementsByClassName('content-section');
            for (var i = 0; i < sections.length; i++) {
                sections[i].classList.remove('active');
            }
            
            var buttons = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].classList.remove('active');
            }
            
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

# Shutdown MT5
if mt5_initialized:
    mt5.shutdown()

print("✓ Dashboard generated successfully!")
