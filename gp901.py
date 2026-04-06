import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# --- 設定區：請在 Render 的 Environment Variables 設定這些值 ---
# 1. LINE Channel Access Token
LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# 統一設定：把這個 ID 當成店裡的「總收件地址」
# 確保你在 Render 的 Environment Variables 裡，Key 的名稱是 LINE_DESTINATION_ID
LINE_DESTINATION_ID = os.environ.get('LINE_DESTINATION_ID')

line_bot_api = LineBotApi(LINE_TOKEN)

@app.route("/webhook", methods=['POST'])
def handle_tire_order():
    data = request.json
    if not data: return "No Data", 400
    print(f"📦 收到【輪胎系統】請求")

    # --- 關鍵修正：定義 target_id ---
    # 它會按順序找：AppSheet 傳來的 target_id -> AppSheet 傳來的 lineid -> Render 的預設 ID
    target_id = data.get('target_id') or data.get('lineid') or LINE_DESTINATION_ID

    store = data.get('store', '未知店家')
    order_list = data.get('order_list', [])

    # ...中間組裝訊息的程式碼照舊...

    try:
        # 現在這裡有 target_id 了，就不會再報錯
        line_bot_api.push_message(target_id, TextSendMessage(text=msg))
        return "OK", 200
    except Exception as e:
        print(f"❌ 輪胎發送失敗：{e}")
        return "Line API Error", 500
if __name__ == "__main__":
    # 這行是讓 Render 自動分配門牌號碼
    import os
    port = int(os.environ.get("PORT", 5000))
    # host 必須是 '0.0.0.0'，不能是 '127.0.0.1'
    app.run(host='0.0.0.0', port=port)