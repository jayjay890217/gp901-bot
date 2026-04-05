import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# --- 設定區：請在 Render 的 Environment Variables 設定這些值 ---
# 1. LINE Channel Access Token
LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
# 2. 你的 LINE User ID (或是要接收訊息的群組 ID)
USER_ID = os.environ.get('USER_ID')

line_bot_api = LineBotApi(LINE_TOKEN)

@app.route("/webhook", methods=['POST'])
def webhook():
    # 接收來自 AppSheet 的 JSON 資料
    data = request.json
    if not data:
        return "No Data", 400

    store = data.get('store', '未知店家')
    order_list = data.get('order_list', [])

    # 1. 建立訊息標題
    msg = f"📦 【旭馳車業】批量叫料通知\n"
    msg += f"發報店家：{store}\n"
    msg += "--------------------------\n"

    # 2. 解析每一筆輪胎清單
    if not order_list:
        msg += "⚠️ 目前清單中無待發報項目"
    else:
        for i, item in enumerate(order_list, 1):
            # 如果 AppSheet 傳過來的是字串，則解析成 dict
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except:
                    msg += f"{i}. 資料格式異常\n"
                    continue
            
            spec = item.get('spec', '未知規格')
            size = item.get('size', '未知尺寸')
            qty = item.get('qty', 0)
            
            msg += f"{i}. {spec} - {size} * {qty}條\n"

    msg += "--------------------------\n"
    msg += "請盡速處理，謝謝。"

    # 3. 發送到 LINE
    try:
        line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
        print("LINE 訊息發送成功！")
    except Exception as e:
        print(f"發送失敗：{e}")
        return "Line API Error", 500

    return "OK", 200

if __name__ == "__main__":
    # 這行是讓 Render 自動分配門牌號碼
    import os
    port = int(os.environ.get("PORT", 5000))
    # host 必須是 '0.0.0.0'，不能是 '127.0.0.1'
    app.run(host='0.0.0.0', port=port)