import os
import yfinance as yf
from datetime import datetime
from model import Kronos, KronosTokenizer, KronosPredictor 

# 1. Initialize Kronos
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 2. Read tickers from your asset list
with open("tracked_assets.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

# 3. Start building the HTML String with CSS Styling
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kronos AI Market Matrix</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background-color: #ffffff; color: #37352f; padding: 20px; margin: 0; }}
        h1 {{ font-size: 24px; margin-bottom: 5px; color: #191919; }}
        .timestamp {{ font-size: 13px; color: #787774; margin-bottom: 25px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th {{ background-color: #f7f6f3; text-align: left; padding: 12px 16px; font-weight: 600; font-size: 14px; color: #5a5a57; border-bottom: 1px solid #e9e8e4; }}
        td {{ padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #edebe9; }}
        tr:hover {{ background-color: #fbfbfa; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: 500; font-size: 12px; }}
        .bullish {{ background-color: #e2f6ed; color: #237c53; }}
        .bearish {{ background-color: #ffebe9; color: #d12e27; }}
    </style>
</head>
<body>

    <h1>📈 Kronos AI Analytics Interface</h1>
    <div class="timestamp">Matrix Engine Active • Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>

    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Current Price</th>
                <th>Trend Prediction</th>
                <th>Confidence Signal</th>
            </tr>
        </thead>
        <tbody>
"""

# 4. Generate dynamic rows
for ticker in tickers:
    try:
        data = yf.download(ticker, period="60d", interval="1d")
        if data.empty: continue
        
        current_price = f"${data['Close'].iloc[-1]:.2f}"
        prediction = predictor.predict(data) 
        
        if prediction['direction'] == 1:
            trend_html = '<span class="badge bullish">🟩 Bullish</span>'
        else:
            trend_html = '<span class="badge bearish">🟥 Bearish</span>'
            
        confidence = f"{prediction['probability'] * 100:.1f}%"
        
        html_content += f"""
            <tr>
                <td><strong>{ticker}</strong></td>
                <td>{current_price}</td>
                <td>{trend_html}</td>
                <td>{confidence}</td>
            </tr>"""
    except Exception as e:
        html_content += f"<tr><td><strong>{ticker}</strong></td><td>Error</td><td><span class='badge'>Failed</span></td><td>N/A</td></tr>"

# 5. Close HTML Tags and save file
html_content += """
        </tbody>
    </table>
</body>
</html>
"""

with open("notion_index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML Dashboard successfully compiled into notion_index.html!")
