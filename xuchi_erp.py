from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from urllib.parse import quote, unquote, urlparse, parse_qs
import json

app = Flask(__name__)

# --- 請填入你的 LINE 代碼 ---
import os  # 在檔案最上面加入這行
# ... 其他 import ...

# 改成用 os.environ 去抓取
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_DESTINATION_ID = os.environ.get('LINE_DESTINATION_ID')
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

@app.route('/appsheet_webhook', methods=['POST'])
def handle_appsheet():
    data = request.json
    print("\n" + "="*30)
    print("🚀 收到 AppSheet 封包")
    
    # 1. 抓取資料 (修正變數未定義問題)
    plate = data.get('plate') or '未知車牌'
    customer = data.get('customer') or '未知客戶'
    doc_type = data.get('doc_type') or '未知文件'
    raw_image_path = data.get('image_name', '')

    # 2. 【核心修正】從長網址中提取真正的檔案名稱
    # 因為 AppSheet 給的是網址，我們要抓出 fileName= 後面的部分
    if "fileName=" in raw_image_path:
        parsed_url = urlparse(raw_image_path)
        actual_file_name = parse_qs(parsed_url.query).get('fileName', [''])[0]
    else:
        actual_file_name = raw_image_path
    
    # 確保路徑是乾淨的
    actual_file_name = unquote(actual_file_name)

    # 3. 組合圖片網址
    app_id = "f8297f93-348b-44d5-8831-8e9b7e95a1ea"
    table_encoded = quote("文件明細表")
    file_encoded = quote(actual_file_name, safe='/')
    
    image_url = f"https://www.appsheet.com/template/gettablefileurl?appName={app_id}&tableName={table_encoded}&fileName={file_encoded}"
    
    print(f"📌 車牌：{plate} | 客戶：{customer}")
    print(f"🔍 最終圖片網址：{image_url}")

    # 4. 製作 LINE 卡片
    flex_contents = {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "🚗 旭馳車業 - 新文件上傳", "weight": "bold", "color": "#1DB446"}]
        },
        "hero": {
            "type": "image", "url": image_url, "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        },
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"車牌：{plate}", "weight": "bold", "size": "xl"},
                {"type": "text", "text": f"客戶：{customer}", "size": "md", "margin": "md"},
                {"type": "text", "text": f"類別：{doc_type}", "size": "sm", "color": "#888888", "margin": "sm"}
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "uri", "label": "點我查看原圖", "uri": image_url}, "style": "primary", "color": "#1DB446"}
            ]
        }
    }

    try:
        line_bot_api.push_message(
            LINE_DESTINATION_ID,
            FlexSendMessage(alt_text=f"車號 {plate} 有新文件", contents=flex_contents)
        )
        print("✅ LINE 發送成功！")
    except Exception as e:
        print(f"❌ LINE 發送失敗：{e}")

    return jsonify({"status": "success"}), 200

# 只要留下這一行就好，讓 Flask 實例活著
app = app