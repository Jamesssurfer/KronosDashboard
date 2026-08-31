import os
import yfinance as yf
from datetime import datetime

# 1. Read tickers from your asset list
try:
    with open("tracked_assets.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    tickers = ["AAPL", "NVDA", "BTC-USD", "SPY"]

# 2. Build Dashboard Header (Overall tab removed completely)
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kronos Analysis Dashboard</title>
    <!-- Include Chart.js for rendering live historical visual charts -->
    <script src="https://jsdelivr.net"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 25px; margin: 0; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ font-size: 22px; color: #ffffff; margin: 0; font-weight: 600; }}
        .meta-info {{ font-size: 12px; color: #94a3b8; text-align: right; }}
        
        /* Navigation Tabs Layout */
        .tabs-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 25px; }}
        .tab-btn {{ background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 8px 16px; font-family: inherit; font-size: 13px; cursor: pointer; border-radius: 6px; transition: all 0.2s; }}
        .tab-btn:hover {{ background-color: #334155; color: #f8fafc; }}
        .tab-btn.active {{ background-color: #2563eb; color: #ffffff; border-color: #3b82f6; font-weight: 600; }}

        /* Main Data Container Panels */
        .grid-layout {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
        .panel {{ background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }}
        .panel-title {{ font-size: 14px; font-weight: 600; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 8px; }}
        
        /* Metric Styling */
        .metric-card {{ background-color: #1f2937; border-radius: 6px; padding: 15px; margin-bottom: 15px; border-left: 4px solid #3b82f6; }}
        .metric-label {{ font-size: 12px; color: #94a3b8; margin-bottom: 4px; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #ffffff; }}
        
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block; margin-top: 5px; }}
        .bullish {{ background-color: #10b98120; color: #34d399; border: 1px solid #34d39940; }}
        .bearish {{ background-color: #ef444420; color: #f87171; border: 1px solid #f8717140; }}
        
        .chart-container {{ position: relative; width: 100%; height: 320px; }}
        
        .content-section {{ display: none; }}
        .content-section.active {{ display: block; }}
    </style>
</head>
<body>

    <div class="header">
        <h1>Kronos Analysis Dashboard</h1>
        <div class="meta-info">
            Data Matrix Active<br>
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>

    <!-- Assets Navigation Tabs -->
    <div class="tabs-container">
"""

# Append asset buttons only (Overall tab is gone)
for index, ticker in enumerate(tickers):
    active_class = "active" if index == 0 else ""
    html_content += f'        <button class="tab-btn {active_class}" onclick="switchTab(\'tab-{index}\')">{ticker}</button>\n'

html_content += """    </div>\n"""

# 3. Generate Analytical Panels and Real Visual Charts for each asset
for index, ticker in enumerate(tickers):
    active_section = "active" if index == 0 else ""
    
    # Initialize fallback default values
    current_price = "N/A"
    price_change_pct = 0.0
    direction_bias = "Neutral"
    bias_style = "bullish"
    historical_closes = []
    historical_dates = []
    
    try:
        # Fetch 30 days of actual historical price data sequence matching the model style input
        stock_data = yf.download(ticker, period="30d", interval="1d")
        if not stock_data.empty:
            closes = stock_data['Close'].dropna().tolist()
            dates = [d.strftime('%m-%d') for d in stock_data.index]
            
            current_price = f"${closes[-1]:.2f}"
            price_change_pct = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            
            # Trend mathematical assessment metrics
            # Calculates short-term price momentum bias (similar to foundation time-series token parsing)
            short_ema = sum(closes[-5:]) / 5
            long_ema = sum(closes[-20:]) / 20
            
            if short_ema > long_ema:
                direction_bias = "Bullish Data Trend"
                bias_style = "bullish"
            else:
                direction_bias = "Bearish Data Trend"
                bias_style = "bearish"
                
            historical_closes = closes
            historical_dates = dates
    except Exception as e:
        current_price = "Connection Error"

    html_content += f"""
    <!-- PANEL FOR {ticker} -->
    <div id="tab-{index}" class="content-section {active_section}">
        <div class="grid-layout">
            
            <!-- Technical Metrics Column -->
            <div class="panel">
                <div class="panel-title">{ticker} Data Statistics</div>
                
                <div class="metric-card">
                    <div class="metric-label">Last Tracked Close Price</div>
                    <div class="metric-value">{current_price}</div>
                </div>
                
                <div class="metric-card" style="border-left-color: {'#34d399' if price_change_pct >= 0 else '#f87171'};">
                    <div class="metric-label">Daily Price Move</div>
                    <div class="metric-value" style="color: {'#34d399' if price_change_pct >= 0 else '#f87171'};">
                        {price_change_pct:+.2f}%
                    </div>
                </div>
                
                <div class="metric-card" style="border-left-color: {'#34d399' if bias_style == 'bullish' else '#f87171'};">
                    <div class="metric-label">Calculated Directional Bias</div>
                    <span class="badge {bias_style}">{direction_bias}</span>
                </div>
            </div>
            
            <!-- Real Visual Trend Line Chart Column -->
            <div class="panel">
                <div class="panel-title">{ticker} Historical Price Matrix (30 Days)</div>
                <div class="chart-container">
                    <canvas id="chart-{index}"></canvas>
                </div>
            </div>
            
        </div>
    </div>
    
    <script>
        // Draw the visualization plot chart context sequentially
        new Chart(document.getElementById('chart-{index}'), {{
            type: 'line',
            data: {{
                labels: {str(historical_dates)},
                datasets: [{{
                    label: '{ticker} Price',
                    data: {str(historical_closes)},
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointRadius: 2,
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

# 4. Inject Dynamic Interactivity Scripts into Dashboard footer
html_content += """
    <script>
        function switchTab(tabId) {
            var sections = document.getElementsByClassName('content-section');
            for (var i = 0; i < sections.length; i++) {
                sections[i].classList.remove('active');
            }
            
            var buttons = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].classList.remove('active');
            }
            
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
"""

# Save out compiled file layout
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Visual Chart Dashboard compiled successfully.")
