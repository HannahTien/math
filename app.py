import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # 使用最新且反應最快的模型
    model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not api_key:
        return jsonify({"reply": "系統發生錯誤：未設定 API Key"}), 500

    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"reply": "請輸入問題喔！"}), 400

    # 🌟 重新洗腦：專業、俐落的正常老師
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)