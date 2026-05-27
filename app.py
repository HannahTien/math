from flask import Flask, render_template

# 建立 Flask 網站物件
app = Flask(__name__)

# 設定首頁路由 (當使用者連到網站網址時，要做什麼事)
@app.route('/')
def home():
    # 回傳 templates 資料夾裡面的 index.html 檔案
    return render_template('index.html')

# 啟動伺服器
if __name__ == '__main__':
    # debug=True 代表你改了程式碼存檔後，網站會自動重新載入，不用一直重開
    app.run(debug=True)