from fastapi import FastAPI, Request
from database import SessionLocal, engine
from models import Base, Trade
from telegram_bot import send_message
from config import API_SECRET
import json

app = FastAPI()

# إنشاء الجداول تلقائياً عند تشغيل السيرفر
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"status": "Server Running 🚀", "owner": "Iyad Nabil"}

# دالة أساسية لتنظيف بيانات الـ JSON (حل مشكلة Extra Data)
async def get_clean_json(request: Request):
    try:
        raw_body = await request.body()
        # تحويل البيانات لنص وتنظيفها من الفراغات والرموز الصفرية \0
        clean_body = raw_body.decode('utf-8').strip().replace('\x00', '')
        return json.loads(clean_body)
    except Exception as e:
        print(f"❌ Error decoding JSON: {e}")
        return None

# ===============================
# 1. فتح صفقة جديدة
# ===============================
@app.post("/trade/open")
async def open_trade(request: Request):
    data = await get_clean_json(request)
    
    if not data or data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()
    try:
        ticket = str(data.get("ticket"))

        # منع تكرار تسجيل نفس الصفقة
        existing = db.query(Trade).filter(Trade.ticket == ticket).first()
        if existing:
            return {"message": "Already exists"}

        trade = Trade(
            ticket=ticket,
            symbol=data.get("symbol"),
            type=data.get("type"),
            lot=data.get("lot"),
            entry=data.get("entry"),
            sl=data.get("sl"),
            tp=data.get("tp"),
            status="OPEN"
        )

        db.add(trade)
        db.commit()

        # إرسال إشعار للمشتركين في القناة
        msg = (f"🔔 <b>صفقة جديدة</b>\n\n"
               f"🎯 الزوج: {trade.symbol}\n"
               f"🛠 النوع: {trade.type}\n"
               f"💰 الدخول: {trade.entry}\n"
               f"🛑 SL: {trade.sl}\n"
               f"✅ TP: {trade.tp}\n"
               f"🆔 #{trade.ticket}")
        
        send_message(msg)
        return {"status": "opened"}
    finally:
        db.close()

# ===============================
# 2. تحديث الصفقة (تعديل SL/TP)
# ===============================
@app.post("/trade/update")
async def update_trade(request: Request):
    data = await get_clean_json(request)

    if not data or data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()
    try:
        trade = db.query(Trade).filter(Trade.ticket == str(data.get("ticket"))).first()

        if not trade:
            return {"error": "Not found"}

        old_sl = trade.sl
        trade.sl = data.get("sl", trade.sl)
        trade.tp = data.get("tp", trade.tp)
        db.commit()

        # إذا تغير الستوب لوز نرسل "تأمين"، وإذا تغير الهدف نرسل "تحديث"
        title = "🔒 <b>تأمين صفقة</b>" if trade.sl != old_sl else "🔄 <b>تحديث أهداف</b>"
        
        msg = (f"{title}\n\n"
               f"🆔 رقم الصفقة: #{trade.ticket}\n"
               f"📍 SL الجديد: {trade.sl}\n"
               f"🎯 TP الجديد: {trade.tp}")
        
        send_message(msg)
        return {"status": "updated"}
    finally:
        db.close()

# ===============================
# 3. إغلاق الصفقة
# ===============================
@app.post("/trade/close")
async def close_trade(request: Request):
    data = await get_clean_json(request)

    if not data or data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()
    try:
        trade = db.query(Trade).filter(Trade.ticket == str(data.get("ticket"))).first()

        if not trade:
            return {"error": "Not found"}

        trade.status = "CLOSED"
        db.commit()

        profit = data.get("profit", 0)
        icon = "✅" if float(profit) >= 0 else "❌"
        
        msg = (f"{icon} <b>إغلاق صفقة #{trade.ticket}</b>\n\n"
               f"📊 النتيجة: {profit} دولار/نقطة\n"
               f"🏁 تم الخروج من السوق.")
        
        send_message(msg)
        return {"status": "closed"}
    finally:
        db.close()
