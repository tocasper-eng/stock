import os
from flask import Flask, render_template_string, request
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

# 解決 Matplotlib 在伺服器環境無顯示器的問題
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# 使用簡單的字典做記憶體緩存，避免重複請求觸發 Rate Limit
data_cache = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>台積電股價分析</title>
    <style>
        body { font-family: "Microsoft JhengHei", sans-serif; background: #f0f2f5; padding: 40px; }
        .card { background: white; max-width: 900px; margin: auto; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .input-group { margin-bottom: 20px; display: flex; gap: 10px; align-items: center; justify-content: center; }
        input { padding: 8px; border-radius: 4px; border: 1px solid #ddd; }
        button { padding: 8px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .msg { text-align: center; color: #666; }
        .error { color: #d9534f; background: #f9d6d5; padding: 10px; border-radius: 4px; text-align: center; }
        img { width: 100%; height: auto; margin-top: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="text-align:center;">台積電 (2330.TW) 歷史股價查詢</h2>
        <form method="POST" class="input-group">
            <input type="date" name="start" value="{{ start }}" required>
            <span>至</span>
            <input type="date" name="end" value="{{ end }}" required>
            <button type="submit">開始繪製</button>
        </form>

        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if chart %}<img src="data:image/png;base64,{{ chart }}">{% endif %}
        <p class="msg">提示：若遇到頻率限制，請稍候 5 分鐘再試。</p>
    </div>
</body>
</html>
"""

def get_stock_data(symbol, start, end):
    cache_key = f"{symbol}_{start}_{end}"
    if cache_key in data_cache:
        return data_cache[cache_key]
    
    # 使用 Ticker 物件下載，穩定性較高
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    
    if not df.empty:
        data_cache[cache_key] = df
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    chart = None
    error = None
    # 預設顯示過去一個月的資料
    default_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end = datetime.now().strftime('%Y-%m-%d')
    
    start_date = request.form.get('start', default_start)
    end_date = request.form.get('end', default_end)

    if request.method == 'POST':
        try:
            df = get_stock_data("2330.TW", start_date, end_date)
            
            if df.empty:
                error = "查無資料或觸發 API 限制。請確認日期區間（週末休市）或稍後再試。"
            else:
                plt.figure(figsize=(12, 6))
                plt.plot(df.index, df['Close'], marker='o', linestyle='-', color='#007bff', label='收盤價')
                plt.title(f'TSMC (2330.TW) Price Trend', fontsize=16)
                plt.xlabel('Date')
                plt.ylabel('Price (TWD)')
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                chart = base64.b64encode(buf.getvalue()).decode('utf-8')
                plt.close()
        except Exception as e:
            error = f"發生錯誤: {str(e)}"

    return render_template_string(HTML_TEMPLATE, chart=chart, error=error, start=start_date, end=end_date)

if __name__ == "__main__":
    # Zeabur 會自動分配 PORT，我們讀取環境變數
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
