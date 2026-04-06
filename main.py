from fastapi import FastAPI, Request
from database import SessionLocal, engine
from models import Base, Trade
from telegram_bot import send_message
from config import API_SECRET
import json

app = FastAPI()
Base.metadata.create_all(bind=engine)

async def get_clean_json(request: Request):
    raw = await request.body()
    return json.loads(raw.decode('utf-8').strip().replace('\x00', ''))

# --- 1. فتح صفقة جديدة ---
@app.post("/trade/open")
async def open_trade(request: Request):
    data = await get_clean_json(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}
    
    db = SessionLocal()
    ticket = str(data["ticket"])
    trade = Trade(ticket=ticket, symbol=data["symbol"], type=data["type"],
                  lot=data["lot"], entry=data["entry"], sl=data.get("sl", 0),
                  tp=data.get("tp", 0), status="OPEN")
    db.merge(trade) # merge لتحديث البيانات إذا كانت موجودة أو إنشاء جديد
    db.commit()
    
    msg = f"🔔 <b>صفقة جديدة مفتوحة</b>\n\n🎯 الزوج: {trade.symbol}\n🛠 النوع: {trade.type}\n💰 الدخول: {trade.entry}\n🆔 #{trade.ticket}"
    send_message(msg)
    db.close()
    return {"status": "opened"}

# --- 2. تحديث (تعديل SL أو TP) ---
@app.post("/trade/update")
async def update_trade(request: Request):
    data = await get_clean_json(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}

    db = SessionLocal()
    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()
    if trade:
        trade.sl = data.get("sl", trade.sl)
        trade.tp = data.get("tp", trade.tp)
        db.commit()
        
        msg = f"🔄 <b>تحديث أهداف الصفقة #{trade.ticket}</b>\n\n🛑 SL: {trade.sl}\n🎯 TP: {trade.tp}\n📢 تم تحديث المستويات بنجاح."
        send_message(msg)
    db.close()
    return {"status": "updated"}

# --- 3. إغلاق الصفقة ---
@app.post("/trade/close")
async def close_trade(request: Request):
    data = await get_clean_json(request)
    if data.get("secret") != API_SECRET: return {"error": "Unauthorized"}

    db = SessionLocal()
    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()
    if trade:
        trade.status = "CLOSED"
        db.commit()
        
        profit = data.get("profit", 0)
        icon = "✅" if float(profit) >= 0 else "❌"
        msg = f"{icon} <b>تم إغلاق الصفقة #{trade.ticket}</b>\n\n📊 النتيجة: {profit} دولار/نقطة"
        send_message(msg)
    db.close()
    return {"status": "closed"}
