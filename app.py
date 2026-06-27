import os
import time
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv()
app = Flask(__name__)

# ==========================================
# 1. Gemini AI 家教設定
# ==========================================
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 2. Render 雲端資料庫設定
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('RENDER_DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class MathFormula(db.Model):
    __tablename__ = 'crawled_formulas'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

# ==========================================
# 3. 網站原本的路由 (完全恢復你原本乾淨的樣子)
# ==========================================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/math')
def math():
    return render_template('math.html')

@app.route('/physics')
def physics():
    return render_template('physics.html')

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not api_key:
        return jsonify({"reply": "系統發生錯誤：未設定 API Key"}), 500

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"reply": "請輸入問題喔！"}), 400

    prompt = f"""
    你現在是一位專業、有耐心的國中理化與數學老師。
    學生的問題是：「{user_message}」

    請嚴格遵守以下對話原則：
    1. 語氣自然、專業、平易近人。絕對不要扮演任何動物角色，不要使用顏文字或奇怪的語尾助詞。
    2. 如果是腦筋急轉彎或邏輯陷阱題（例如一公斤鐵和棉花哪個重），請一針見血地點破盲點，不要生硬地套用物理公式。
    3. 如果是真實的計算題，引導學生思考該用什麼公式，並解釋公式代號，但不要直接給出最終答案。
    4. 格式限制：絕對禁止使用 LaTeX 語法（不要出現任何 $ 符號）。公式請一律使用純文字，例如：W = m * g。
    """

    try:
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"AI 助教目前連線異常，請稍後再試。錯誤代碼：{str(e)}"}), 500

# ==========================================
# 4. 助教版爬蟲功能 (獨立運作，不干擾網頁)
# ==========================================
@app.route('/crawl')
def crawl_formulas():
    print("啟動 Selenium 爬蟲...")
    options = Options()
    options.binary_location = "/usr/bin/chromium" 
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Chrome(options=options)
    target_url = "https://www.scribd.com/document/1009176805/%E5%9C%8B%E4%B8%AD%E6%95%B8%E5%AD%B8%E5%85%AC%E5%BC%8F%E5%92%8C%E9%87%8D%E9%BB%9E%E6%95%B4%E7%90%86-%E8%87%AA%E7%B7%A8"
    
    try:
        driver.get(target_url)
        time.sleep(5)
        for i in range(5):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1.5)
            
        elements = driver.find_elements(By.CSS_SELECTOR, ".text_layer span")
        extracted_text = ""
        for el in elements:
            text = el.text.strip()
            if text:
                extracted_text += text + " "
                
        if extracted_text:
            MathFormula.query.delete() 
            new_data = MathFormula(title="Scribd國中數學公式整理", content=extracted_text)
            db.session.add(new_data)
            db.session.commit()
            print("🎉 雲端資料庫更新成功！")
            # 🌟 照助教的方式，只回傳成功訊息，不渲染任何花俏的網頁
            return "Crawl Success! 爬蟲成功並已存入資料庫！"
        else:
            return "⚠️ 未擷取到文字，請檢查網頁。"

    except Exception as e:
        return f"爬蟲發生錯誤：{e}"
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)