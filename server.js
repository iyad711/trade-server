const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

let lastTrade = {}; 
// --- أضف أرقام الـ ID الخاصة بالمشتركين هنا ---
let subscribers = ["7308459367"]; 
// مخزن لحفظ الـ message_id لعمل Reply لكل مستخدم
let msgHistory = {}; 

// 1. استقبال البيانات من MT5 وتوزيعها
app.post('/trade', async (req, res) => {
    lastTrade = req.body;
    lastTrade.server_time = new Date().toLocaleString();
    
    console.log("✅ استلمت بيانات:", lastTrade.action, "Ticket:", lastTrade.ticket);

    const token = lastTrade.token || "8601737426:AAHZPEJTRu01qteY7dp24mwpN9A4zFLeMUY";

    // إرسال التليجرام لجميع المشتركين
    if (lastTrade.msg) {
        for (let chatId of subscribers) {
            try {
                let url = `https://api.telegram.org/bot${token}/sendMessage`;
                let payload = {
                    chat_id: chatId,
                    text: lastTrade.msg,
                    parse_mode: "Markdown"
                };

                // ميزة الرد الذكي (Reply)
                if (lastTrade.action !== "ORDER_OPEN" && msgHistory[lastTrade.ticket] && msgHistory[lastTrade.ticket][chatId]) {
                    payload.reply_to_message_id = msgHistory[lastTrade.ticket][chatId];
                }

                const response = await axios.post(url, payload);

                // حفظ ID الرسالة الأولى للرد عليها لاحقاً
                if (lastTrade.action === "ORDER_OPEN") {
                    if (!msgHistory[lastTrade.ticket]) msgHistory[lastTrade.ticket] = {};
                    msgHistory[lastTrade.ticket][chatId] = response.data.result.message_id;
                }
            } catch (err) {
                console.error(`❌ فشل الإرسال لـ ${chatId}:`, err.message);
            }
        }
    }

    res.status(200).json({ status: "Success", broadcasted: subscribers.length });
});

// 2. نقطة النسخ (للسلف) - بقيت كما هي لضمان عمل النسخ
app.get('/copy', (req, res) => {
    if (Object.keys(lastTrade).length === 0) {
        res.send("<h1>🛰️ السيرفر يعمل</h1><p>بانتظار أول صفقة...</p>");
    } else {
        res.json(lastTrade); 
    }
});

app.get('/', (req, res) => {
    res.send("<h1>🚀 Hiroshima Multi-User Server is Online</h1>");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
