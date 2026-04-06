from fastapi import FastAPI, Request, HTTPException
from database import SessionLocal, engine
from models import Base, Trade
from telegram_bot import send_message
from config import API_SECRET
import json

app = FastAPI()

# إنشاء الجداول إذا لم تكن موجودة
Base.metadata.create_all(bind=engine)

# الصفحة الرئيسية للتأكد من عمل السيرفر
@app.get("/")
def home():
    return {"status": "Server Running 🚀", "mode": "Production"}

# دالة مساعدة لتنظيف ومعالجة بيانات الـ JSON القادمة من MT5
async def get_clean_json(request: Request):
    try:
        raw_body = await request.body()
        # تنظيف النص من أي رموز زائدة قد يضيفها الميتاتريدر (مثل \0 أو مسافات)
        clean_body = raw_body.decode('utf-8').strip().replace('\x00', '')
        return json.loads(clean_body)
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
        return None

# ===============================
# فتح صفقة
# ===============================
@app.post("/trade/open")
async def open_trade(request: Request):
    data = await get_clean_json(request)
    
    if not data or data.get("secret") != API_SECRET:
        return {"error": "Unauthorized or Invalid JSON"}

    db = SessionLocal()
    try:
        ticket = str(data.get("ticket"))

        # منع تكرار الصفقة
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

        # إرسال الإشعار لتليجرام
        msg = (f"📊 <b>صفقة جديدة</b>\n\n"
               f"الزوج: {trade.symbol}\n"
               f"النوع: {trade.type}\n"
               f"الدخول: {trade.entry}\n"
               f"SL: {trade.sl}\n"
               f"TP: {trade.tp}\n"
               f"رقم الصفقة: #{trade.ticket}")
        
        send_message(msg)
        return {"status": "opened"}
    
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return {"error": str(e)}
    finally:
        db.close()

# ===============================
# تحديث صفقة (SL/TP)
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

        trade.sl = data.get("sl", trade.sl)
        trade.tp = data.get("tp", trade.tp)
        db.commit()

        send_message(f"🔄 <b>تحديث صفقة #{trade.ticket}</b>\n\nSL: {trade.sl}\nTP: {trade.tp}")
        return {"status": "updated"}
    finally:
        db.close()

# ===============================
# إغلاق صفقة
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

        send_message(f"✅ <b>تم إغلاق الصفقة #{trade.ticket}</b>\n\nالنتيجة: {data.get('profit', '0')} نقطة")
        return {"status": "closed"}
    finally:
        db.close()
