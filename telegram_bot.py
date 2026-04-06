import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # CHAT_ID هنا يجب أن يكون ID القناة (مثلاً -100xxxxxxxx) لكي يصل للجميع
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
