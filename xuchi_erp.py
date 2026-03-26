import os
import json
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from urllib.parse import quote, unquote, urlparse, parse_qs

app = Flask(__name__)

# 從雲端環境變數讀取密鑰
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_DESTINATION_ID = os.environ.get('LINE_DESTINATION_ID')
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

@app.route('/appsheet_webhook', methods=['POST'])
def handle_appsheet():
    data = request.json
    case_id = data.get('case_id', '無編號')
    customer = data.get('customer', '未知客戶')
    # 這裡抓取剛才 AppSheet 加 1 後的次數
    update_count = int(data.get('update_count', 1)) 
    
    # --- 自動化標題與配色邏輯 ---
    if update_count <= 1:
        # 第一次發送：綠色專業風格
        header_text = "✨ 旭馳車業 - 首次收件"
        header_color = "#1DB446" # 專業綠
        status_label = "【新案件】"
    else:
        # 修改後發送：橘色提醒風格
        header_text = f"⚠️ 案件修正 (第 {update_count-1} 次)"
        header_color = "#E67E22" # 警告橘
        status_label = f"【修正件 - 第 {update_count-1} 次】"

    # 製作「摘要卡片」
    main_bubble = {
        "type": "bubble", "size": "micro",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_text, "color": "#ffffff", "weight": "bold", "size": "sm"}]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"👤 客戶: {customer}", "weight": "bold", "size": "sm"},
                {"type": "text", "text": status_label, "color": "#e74c3c", "size": "xs", "weight": "bold"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "\n".join(details), "size": "xxs", "wrap": True, "margin": "md"}
            ]
        }
    }
    # ... 後續照片處理邏輯不變 ...
    details = [
        f"📞 電話: {info.get('電話')}",
        f"🏍️ 車種: {info.get('車種')} ({info.get('CC數')}cc)",
        f"🎨 顏色: {info.get('顏色')} / {info.get('款式')}",
        f"💰 付款: {info.get('方式')}",
        f"📝 領牌: {info.get('領牌')}",
        f"🔢 選號: {info.get('選號')}",
        f"♻️ 汰舊: {info.get('汰舊')}"
    ]
    
    main_bubble = {
        "type": "bubble", "size": "micro",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#1DB446",
            "contents": [{"type": "text", "text": "旭馳車業 - 案件摘要", "color": "#ffffff", "weight": "bold", "size": "sm"}]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"👤 客戶: {customer}", "weight": "bold", "size": "sm"},
                {"type": "text", "text": f"🆔 單號: {case_id}", "size": "xxs", "color": "#aaaaaa"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "\n".join(details), "size": "xxs", "wrap": True, "margin": "md"},
                {"type": "text", "text": f"👷 承辦: {staff}", "size": "xxs", "color": "#aaaaaa", "margin": "md"}
            ]
        }
    }
    bubbles = [main_bubble]

    # 2. 製作「照片輪播」
    for label, raw_path in images_dict.items():
        if raw_path and "http" in raw_path:
            parsed_url = urlparse(raw_path)
            actual_file_name = parse_qs(parsed_url.query).get('fileName', [''])[0]
            actual_file_name = unquote(actual_file_name)
            file_encoded = quote(actual_file_name, safe='/')
            image_url = f"https://www.appsheet.com/template/gettablefileurl?appName={app_id}&tableName={table_encoded}&fileName={file_encoded}"

            bubble = {
                "type": "bubble", "size": "micro",
                "hero": { "type": "image", "url": image_url, "size": "full", "aspectRatio": "4:3", "aspectMode": "cover" },
                "body": {
                    "type": "box", "layout": "vertical",
                    "contents": [{"type": "text", "text": label, "weight": "bold", "size": "sm", "align": "center"}]
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "contents": [{"type": "button", "action": {"type": "uri", "label": "原圖", "uri": image_url}, "style": "link", "height": "sm"}]
                }
            }
            bubbles.append(bubble)

    # 打包發送
    flex_contents = {"type": "carousel", "contents": bubbles[:12]} # 摘要1 + 照片11
    line_bot_api.push_message(LINE_DESTINATION_ID, FlexSendMessage(alt_text=f"📁 旭馳案件: {customer}", contents=flex_contents))
    
    return jsonify({"status": "success"}), 200