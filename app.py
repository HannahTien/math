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

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

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
            return "Crawl Success! 爬蟲成功並已存入資料庫！"
        else:
            return "⚠️ 未擷取到文字，請檢查網頁。"

    except Exception as e:
        return f"爬蟲發生錯誤：{e}"
    finally:
        driver.quit()

@app.route('/analyze')
def analyze_data():
    latest_data = MathFormula.query.order_by(MathFormula.created_at.desc()).first()
    
    if not latest_data or not latest_data.content:
        return "<h3>⚠️ 目前雲端資料庫沒有文本可供分析，請先前往 /crawl 執行爬蟲。</h3>"
        
    text_content = latest_data.content
    
    keywords = ["方程式", "三角形", "面積", "函數", "相似", "機率", "圓周率", "絕對值", "平方根", "多項式", "幾何", "座標"]

    analysis_result = {}
    for word in keywords:
        count = text_content.count(word)
        if count > 0:
            analysis_result[word] = count
            
    sorted_result = sorted(analysis_result.items(), key=lambda x: x[1], reverse=True)
    
    html = """
    <div style="font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #2c3e50;">📊 國中數學公式庫：核心概念詞頻分析報表</h2>
        <p style="color: #555; line-height: 1.6;">
            本系統對爬蟲取得之無結構化數學文本進行了關鍵字萃取與特徵分析。此量化數據可作為評估各章節公式比重之依據，展現了資料科學與數學專業之結合。
        </p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <tr style="background-color: #f8f9fa; border-bottom: 2px solid #ccc;">
                <th style="padding: 12px;">數學概念關鍵字</th>
                <th style="padding: 12px;">出現次數 (Frequency)</th>
                <th style="padding: 12px; width: 50%;">權重佔比直方圖</th>
            </tr>
    """
    
    max_count = sorted_result[0][1] if sorted_result else 1
    
    for word, count in sorted_result:
        bar_width = int((count / max_count) * 100)
        html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px; font-weight: bold; color: #34495e;">{word}</td>
                <td style="padding: 12px;">{count} 次</td>
                <td style="padding: 12px;">
                    <div style="background-color: #3498db; height: 18px; width: {bar_width}%; border-radius: 3px;"></div>
                </td>
            </tr>
        """
        
    html += """
        </table>
        <p style="margin-top: 20px; font-size: 14px; color: #7f8c8d; text-align: right;">
            <i>* 分析模型：Term Frequency (TF) 特徵提取</i>
        </p>
    </div>
    """
    
    return html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)