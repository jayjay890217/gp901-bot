import os
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from urllib.parse import quote, unquote, urlparse, parse_qs

app = Flask(__name__)

# 從雲端環境變數讀取 (原本設定的 ID 變成「備用地址」)
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_DESTINATION_ID = os.environ.get('LINE_DESTINATION_ID')
line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)

# 抓取 LINE 群組 ID 的窗口 (保留功能)
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    print(f"👂 LINE 傳來訊息了: {body}") 
    return 'OK'

@app.route('/appsheet_webhook', methods=['POST'])
def handle_appsheet():
    data = request.json
    print(f"🚀 收到 AppSheet 請求內容: {data}")

    # --- 1. 動態收件人導航 ---
    # 優先拿 AppSheet 傳來的 target_id，如果沒傳才用 Render 預設的備用 ID
    target_id = data.get('target_id') or LINE_DESTINATION_ID

    case_id = data.get('case_id', '無編號')
    customer = data.get('customer', '未知客戶')
    update_count = int(data.get('update_count', 0))
    info = data.get('info', {})
    images_dict = data.get('images', {})
    
    app_id = "f8297f93-348b-44d5-8831-8e9b7e95a1ea"
    table_encoded = quote("文件明細表") 

    # --- 2. 整理摘要文字 (修正空值問題，讓沒填的地方顯示「未填」) ---
    details_list = [
        f"🏍️ 廠牌: {info.get('廠牌') or '未填'}",
        f"📞 電話: {info.get('電話') or '未填'}",
        f"🏍️ 車種: {info.get('車種') or '未填'} ({info.get('CC數') or '-'})",
        f"🎨 顏色: {info.get('顏色') or '未填'} / {info.get('款式') or '-'}",
        f"💰 付款: {info.get('方式') or '未填'} ({info.get('期數') or '-'})",
        f"📝 領牌: {info.get('領牌') or '未填'}",
        f"🔢 選號: {info.get('選號') or '無'}",
        f"♻️ 汰舊: {info.get('汰舊') or '無'}"  
    ]
    info_text = "\n".join(details_list)

    # --- 3. 判斷標題與顏色 ---
    if update_count <= 1:
        header_text = "✨ 旭馳車業 - 首次新件"
        header_color = "#1DB446" # 綠色
    else:
        header_text = f"⚠️ 案件修正 (第 {update_count-1} 次)"
        header_color = "#E67E22" # 橘色

    # --- 4. 製作摘要卡片 (MEGA 尺寸 + 大字強化) ---
    bubbles = [{
        "type": "bubble", 
        "size": "mega", 
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": header_color,
            "contents": [{"type": "text", "text": header_text, "color": "#ffffff", "weight": "bold", "size": "md"}]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                # 客戶姓名加大 (lg) 並加粗
                {"type": "text", "text": f"👤 客戶: {customer}", "weight": "bold", "size": "lg", "color": "#111111"},
                {"type": "separator", "margin": "md"},
                # 內容細節加大 (sm) 並增加行距
                {"type": "text", "text": info_text, "size": "sm", "wrap": True, "margin": "md", "lineSpacing": "6px"}, 
                {"type": "separator", "margin": "md"},
                # 單號與上傳人員小字處理
                {"type": "text", "text": f"單號: {case_id} / 人員: {data.get('staff', '系統')}", "size": "xxs", "color": "#aaaaaa"}
            ]
        }
    }]

    # --- 5. 製作照片卡片 (也必須是 MEGA 尺寸) ---
    for label, raw_path in images_dict.items():
        if raw_path and "http" in raw_path:
            # 沿用你原本精準的圖片路徑解析邏輯
            parsed_url = urlparse(raw_path)
            actual_file_name = parse_qs(parsed_url.query).get('fileName', [''])[0]
            actual_file_name = unquote(actual_file_name)
            file_encoded = quote(actual_file_name, safe='/')
            image_url = f"https://www.appsheet.com/template/gettablefileurl?appName={app_id}&tableName={table_encoded}&fileName={file_encoded}"

            bubbles.append({
                "type": "bubble", 
                "size": "mega",
                "hero": { 
                    "type": "image", "url": image_url, "size": "full", "aspectRatio": "4:3", "aspectMode": "cover" 
                },
                "body": { 
                    "type": "box", "layout": "vertical", 
                    "contents": [{"type": "text", "text": label, "weight": "bold", "size": "md", "align": "center"}] 
                },
                "footer": { 
                    "type": "box", "layout": "vertical", 
                    "contents": [{"type": "button", "action": {"type": "uri", "label": "點我下載高清原圖", "uri": image_url}, "style": "primary", "height": "sm"}] 
                }
            })

    # --- 6. 正式發送 (發送到指定的 target_id) ---
    if len(bubbles) > 0 and target_id:
        flex_contents = {"type": "carousel", "contents": bubbles[:12]}
        try:
            line_bot_api.push_message(target_id, FlexSendMessage(alt_text=f"📁 旭馳新件: {customer}", contents=flex_contents))
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print(f"❌ LINE發送錯誤: {e}")
            return jsonify({"status": "line_error", "msg": str(e)}), 500
    
    return jsonify({"status": "no_destination_or_data"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)