from fastapi import FastAPI, Request
from database import SessionLocal, engine
from models import Base, Trade
from telegram_bot import send_message
from config import API_SECRET
import json

app = FastAPI()
Base.metadata.create_all(bind=engine)

# دالة لتنظيف بيانات الميتاتريدر من أي رموز زائدة
async def clean_data(request: Request):
    raw = await request.body()
    return json.loads(raw.decode('utf-8').strip().replace('\x00', ''))

@app.post("/trade/open")
async def open_trade(request: Request):
    data = await clean_data(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}
    
    db = SessionLocal()
    ticket = str(data["ticket"])
    if db.query(Trade).filter(Trade.ticket == ticket).first():
        db.close()
        return {"message": "Exists"}

    trade = Trade(ticket=ticket, symbol=data["symbol"], type=data["type"],
                  lot=data["lot"], entry=data["entry"], sl=data.get("sl"),
                  tp=data.get("tp"), status="OPEN")
    db.add(trade)
    db.commit()
    
    send_message(f"🔔 <b>فتح صفقة جديدة</b>\n\n🎯 الزوج: {trade.symbol}\n🛠 النوع: {trade.type}\n💰 الدخول: {trade.entry}\n🛑 SL: {trade.sl}\n✅ TP: {trade.tp}\n🆔 #{trade.ticket}")
    db.close()
    return {"status": "opened"}

@app.post("/trade/update")
async def update_trade(request: Request):
    data = await clean_data(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}

    db = SessionLocal()
    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()
    if not trade: 
        db.close()
        return {"error": "Not found"}

    old_sl = trade.sl
    trade.sl = data.get("sl", trade.sl)
    trade.tp = data.get("tp", trade.tp)
    db.commit()

    # رسالة ذكية للتأمين
    status_msg = "🔒 <b>تعديل/تأمين الصفقة</b>" if trade.sl != old_sl else "🔄 <b>تحديث الأهداف</b>"
    
    send_message(f"{status_msg}\n\n🆔 رقم الصفقة: #{trade.ticket}\n📍 SL الجديد: {trade.sl}\n🎯 TP الجديد: {trade.tp}")
    db.close()
    return {"status": "updated"}

@app.post("/trade/close")
async def close_trade(request: Request):
    data = await clean_data(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}

    db = SessionLocal()
    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()
    if not trade: 
        db.close()
        return {"error": "Not found"}

    trade.status = "CLOSED"
    db.commit()
    
    profit = data.get("profit", 0)
    icon = "✅" if float(profit) >= 0 else "❌"
    
    send_message(f"{icon} <b>إغلاق صفقة #{trade.ticket}</b>\n\n📊 النتيجة: {profit} نقطة/دولار\n🏁 تم خروج السعر من السوق.")
    db.close()
    return {"status": "closed"}
