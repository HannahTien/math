import os
import google.generativeai as genai
from dotenv import load_dotenv

# 載入你的 API Key
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("🔍 正在連線 Google 伺服器尋找可用模型...")
try:
    for m in genai.list_models():
        # 篩選出可以用來「生成對話內容」的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 找到可用模型：{m.name}")
    print("✨ 尋找結束！")
except Exception as e:
    print("❌ 連線發生錯誤：", e)