import os
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from urllib.parse import quote, unquote, urlparse, parse_qs

app = Flask(__name__)

# 從雲端環境變數讀取
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_DESTINATION_ID = os.environ.get('LINE_DESTINATION_ID')
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

# 這是專門用來抓 LINE 群組 ID 的門
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    print(f"👂 LINE 傳來訊息了: {body}") # 這行會把群組 ID 噴在 Logs 裡
    return 'OK'

@app.route('/appsheet_webhook', methods=['POST'])
def handle_appsheet():
    data = request.json
    print(f"🚀 收到 AppSheet 請求內容: {data}")

    case_id = data.get('case_id', '無編號')
    customer = data.get('customer', '未知客戶')
    update_count = int(data.get('update_count', 0))
    info = data.get('info', {})
    images_dict = data.get('images', {})
    
    app_id = "f8297f93-348b-44d5-8831-8e9b7e95a1ea"
    table_encoded = quote("文件明細表") 

    # 1. 整理摘要文字 (確保名稱對齊，不會報錯)
    details_list = [
        f"📞 電話: {info.get('電話', '未填')}",
        f"🏍️ 車種: {info.get('車種', '未填')} ({info.get('CC數', '-')})",
        f"🎨 顏色: {info.get('顏色', '未填')} / {info.get('款式', '-')}",
        f"💰 付款: {info.get('方式', '未填')}",
        f"📝 領牌: {info.get('領牌', '未填')}",
        f"🔢 選號: {info.get('選號', '無')}",
        f"♻️ 汰舊: {info.get('汰舊', '無')}"
    ]
    info_text = "\n".join(details_list)

    # 2. 判斷標題與顏色
    if update_count <= 1:
        header_text = "✨ 旭馳車業 - 首次新件"
        header_color = "#1DB446" 
    else:
        header_text = f"⚠️ 案件修正 (第 {update_count-1} 次)"
        header_color = "#E67E22"

    # 3. 製作摘要卡片
    bubbles = [{
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_text, "color": "#ffffff", "weight": "bold", "size": "sm"}]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"👤 客戶: {customer}", "weight": "bold", "size": "sm"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": info_text, "size": "xxs", "wrap": True, "margin": "md"},
                {"type": "text", "text": f"單號: {case_id}", "size": "xxs", "color": "#aaaaaa"}
            ]
        }
    }]

    # 4. 製作照片卡片
    for label, raw_path in images_dict.items():
        if raw_path and "http" in raw_path:
            parsed_url = urlparse(raw_path)
            actual_file_name = parse_qs(parsed_url.query).get('fileName', [''])[0]
            actual_file_name = unquote(actual_file_name)
            file_encoded = quote(actual_file_name, safe='/')
            image_url = f"https://www.appsheet.com/template/gettablefileurl?appName={app_id}&tableName={table_encoded}&fileName={file_encoded}"

            bubbles.append({
                "type": "bubble", "size": "mega",
                "hero": { "type": "image", "url": image_url, "size": "full", "aspectRatio": "4:3", "aspectMode": "cover" },
                "body": { "type": "box", "layout": "vertical", "contents": [{"type": "text", "text": label, "weight": "bold", "size": "sm", "align": "center"}] },
                "footer": { "type": "box", "layout": "vertical", "contents": [{"type": "button", "action": {"type": "uri", "label": "原圖", "uri": image_url}, "style": "link", "height": "sm"}] }
            })

    # 5. 發送
    if len(bubbles) > 0:
        flex_contents = {"type": "carousel", "contents": bubbles[:12]}
        try:
            line_bot_api.push_message(LINE_DESTINATION_ID, FlexSendMessage(alt_text=f"📁 旭馳新件: {customer}", contents=flex_contents))
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print(f"❌ LINE發送錯誤: {e}")
            return jsonify({"status": "line_error", "msg": str(e)}), 500
    
    return jsonify({"status": "no_data"}), 200