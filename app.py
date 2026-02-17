from flask import Flask, render_template_string, request, send_file
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)

# HTML 模板，用於接收日期輸入和顯示圖表
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台積電股價圖表</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
        .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 800px; margin: auto; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        form { display: flex; flex-direction: column; gap: 15px; margin-bottom: 30px; }
        label { font-weight: bold; color: #555; }
        input[type="date"] { padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 16px; }
        button { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; transition: background-color 0.3s ease; }
        button:hover { background-color: #0056b3; }
        .error { color: red; text-align: center; margin-top: 20px; }
        .chart-container { text-align: center; margin-top: 30px; }
        .chart-container img { max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 4px; }
        .footer { text-align: center; margin-top: 40px; color: #777; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>台積電 (2330.TW) 股價查詢</h1>

        <form method="POST">
            <label for="start_date">開始日期:</label>
            <input type="date" id="start_date" name="start_date" value="{{ start_date | default(today) }}" required>

            <label for="end_date">結束日期:</label>
            <input type="date" id="end_date" name="end_date" value="{{ end_date | default(today) }}" required>

            <button type="submit">查詢並繪製圖表</button>
        </form>

        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if chart_img %}
            <h2>股價走勢圖</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{{ chart_img }}" alt="台積電股價圖表">
            </div>
        {% endif %}
    </div>
    <div class="footer">
        <p>資料來源: Yahoo Finance</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    chart_img = None
    error = None
    today = datetime.now().strftime('%Y-%m-%d')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if request.method == 'POST' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

            if start_date > end_date:
                error = "開始日期不能晚於結束日期。"
            else:
                # 爬取台積電股價 (2330.TW)
                df = yf.download("2330.TW", start=start_date_str, end=end_date_str)

                if df.empty:
                    error = "在指定日期區間內沒有找到台積電的股價資料。"
                else:
                    # 繪製圖表
                    plt.figure(figsize=(12, 6))
                    plt.plot(df.index, df['Adj Close'], label='調整後收盤價', color='blue')
                    plt.title(f'台積電 (2330.TW) 股價走勢圖 ({start_date_str} to {end_date_str})')
                    plt.xlabel('日期')
                    plt.ylabel('股價 (TWD)')
                    plt.grid(True)
                    plt.legend()
                    plt.xticks(rotation=45)
                    plt.tight_layout()

                    # 將圖表保存到記憶體並轉為 base64 編碼
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png')
                    img_buffer.seek(0)
                    chart_img = base64.b64encode(img_buffer.read()).decode('utf-8')
                    plt.close() # 關閉圖表以釋放記憶體

        except Exception as e:
            error = f"處理請求時發生錯誤: {e}"

    return render_template_string(HTML_TEMPLATE, 
                                  chart_img=chart_img, 
                                  error=error,
                                  today=today,
                                  start_date=start_date_str,
                                  end_date=end_date_str)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
