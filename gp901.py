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

    # 1. 抓取地址
    target_id = data.get('target_id') or data.get('lineid') or BACKUP_ID
    
    # 2. 【關鍵修正】先初始化 msg 變數，防止它「未定義」
    store = data.get('store', '未知店家')
    msg = f"📦 【旭馳車業】批量叫料通知\n發報店家：{store}\n--------------------------\n"

    # 3. 處理清單內容
    order_list = data.get('order_list', [])
    if not order_list:
        msg += "⚠️ 目前清單中無待發報項目\n"
    else:
        # 如果 AppSheet 傳來的是字串格式，先轉成清單
        if isinstance(order_list, str):
            try:
                order_list = json.loads(order_list)
            except:
                pass
        
        # 3. 處理清單內容 (加強版)
    order_list = data.get('order_list', [])
    print(f"🧐 收到清單內容: {order_list}") # 這行會幫我們在 Logs 抓出兇手

    if not order_list or len(order_list) == 0:
        msg += "⚠️ 目前清單中無待發報項目\n"
    else:
        # 如果 AppSheet 傳來的是單一字串，先轉成清單
        if isinstance(order_list, str):
            try:
                order_list = json.loads(order_list)
            except:
                order_list = [order_list] # 真的轉不動就當成一筆資料
        
        for i, item in enumerate(order_list, 1):
            # --- 關鍵修正：如果 item 是字串，嘗試再解析一次 ---
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except:
                    # 如果不是 JSON 格式，就直接把字串印出來
                    msg += f"{i}. {item}\n"
                    continue
            
            # 抓取資料 (不管欄位叫什麼都試試看)
            spec = item.get('spec') or item.get('輪胎規格') or '規格未填'
            size = item.get('size') or item.get('輪胎尺寸') or '尺寸未填'
            qty = item.get('qty') or item.get('數量') or 0
            
            # 跳過結尾標記
            if item.get('is_end') == "true": continue 
            
            msg += f"{i}. {spec} / {size} * {qty}條\n"

    msg += "--------------------------\n請盡速處理，謝謝。"

    # 4. 發送訊息
    try:
        if not target_id:
            raise ValueError("找不到收件地址 (target_id)")
            
        line_bot_api.push_message(target_id, TextSendMessage(text=msg))
        print("✅ LINE 訊息發送成功！")
        return "OK", 200
    except Exception as e:
        # 這裡會印出為什麼失敗，幫助我們排查
        print(f"❌ 輪胎發送失敗：{str(e)}")
        return str(e), 500
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