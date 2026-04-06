from fastapi import FastAPI, Request
from database import SessionLocal, engine
from models import Base, Trade
from telegram_bot import send_message
from config import API_SECRET

app = FastAPI()

Base.metadata.create_all(bind=engine)

# الصفحة الرئيسية
@app.get("/")
def home():
    return {"status": "Server Running 🚀"}


# ===============================
# فتح صفقة
# ===============================
@app.post("/trade/open")
async def open_trade(request: Request):
    data = await request.json()

    if data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()

    ticket = str(data["ticket"])

    # منع التكرار
    existing = db.query(Trade).filter(Trade.ticket == ticket).first()
    if existing:
        return {"message": "Already exists"}

    trade = Trade(
        ticket=ticket,
        symbol=data["symbol"],
        type=data["type"],
        lot=data["lot"],
        entry=data["entry"],
        sl=data.get("sl"),
        tp=data.get("tp"),
        status="OPEN"
    )

    db.add(trade)
    db.commit()

    send_message(f"""
📊 <b>صفقة جديدة</b>

الزوج: {trade.symbol}
النوع: {trade.type}
الدخول: {trade.entry}
SL: {trade.sl}
TP: {trade.tp}
رقم الصفقة: #{trade.ticket}
""")

    return {"status": "opened"}


# ===============================
# تحديث صفقة
# ===============================
@app.post("/trade/update")
async def update_trade(request: Request):
    data = await request.json()

    if data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()

    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()

    if not trade:
        return {"error": "Not found"}

    trade.sl = data.get("sl", trade.sl)
    trade.tp = data.get("tp", trade.tp)

    db.commit()

    send_message(f"""
🔄 <b>تحديث صفقة #{trade.ticket}</b>

SL: {trade.sl}
TP: {trade.tp}
""")

    return {"status": "updated"}


# ===============================
# إغلاق صفقة
# ===============================
@app.post("/trade/close")
async def close_trade(request: Request):
    data = await request.json()

    if data.get("secret") != API_SECRET:
        return {"error": "Unauthorized"}

    db = SessionLocal()

    trade = db.query(Trade).filter(Trade.ticket == str(data["ticket"])).first()

    if not trade:
        return {"error": "Not found"}

    trade.status = "CLOSED"
    db.commit()

    send_message(f"""
✅ <b>تم إغلاق الصفقة #{trade.ticket}</b>

النتيجة: {data.get("profit")} نقطة
""")

    return {"status": "closed"}
