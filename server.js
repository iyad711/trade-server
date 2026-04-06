const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

// ذاكرة السيرفر
let lastTrade = {}; 
let subscribers = new Set(["7308459367"]); // رقمك ثابت لضمان وصول الرسائل لك
let msgHistory = {}; 

const BOT_TOKEN = "8601737426:AAHZPEJTRu01qteY7dp24mwpN9A4zFLeMUY";

// 1. استقبال المشتركين الجدد تلقائياً
app.post('/webhook', (req, res) => {
    if (req.body && req.body.message) {
        const chatId = req.body.message.chat.id.toString();
        if (!subscribers.has(chatId)) {
            subscribers.add(chatId);
            console.log(`👤 مشترك جديد: ${chatId}`);
            axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                chat_id: chatId,
                text: "✅ تم تفعيل اشتراكك في Hiroshima 711 بنجاح!"
            }).catch(e => console.log("Welcome msg failed"));
        }
    }
    res.sendStatus(200);
});

// 2. استقبال وتوزيع التوصيات والنسخ
app.post('/trade', async (req, res) => {
    lastTrade = req.body;
    lastTrade.server_time = new Date().toLocaleString();
    
    console.log("✅ استلمت بيانات:", lastTrade.action);

    if (lastTrade.msg) {
        const userList = Array.from(subscribers);
        for (let chatId of userList) {
            try {
                let payload = {
                    chat_id: chatId,
                    text: lastTrade.msg,
                    parse_mode: "Markdown"
                };

                // ميزة الرد (Reply) لكل مستخدم
                if (lastTrade.action !== "ORDER_OPEN" && msgHistory[lastTrade.ticket] && msgHistory[lastTrade.ticket][chatId]) {
                    payload.reply_to_message_id = msgHistory[lastTrade.ticket][chatId];
                }

                const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, payload);

                // حفظ رقم الرسالة الأولى للردود المستقبلية
                if (lastTrade.action === "ORDER_OPEN") {
                    if (!msgHistory[lastTrade.ticket]) msgHistory[lastTrade.ticket] = {};
                    msgHistory[lastTrade.ticket][chatId] = response.data.result.message_id;
                }
            } catch (err) {
                console.error(`❌ خطأ إرسال لـ ${chatId}:`, err.message);
            }
        }
    }
    res.status(200).json({ status: "Success" });
});

// 3. مسار النسخ (للسليف) - لضمان عمل الناسخ من MT5 إلى MT5
app.get('/copy', (req, res) => {
    res.json(lastTrade); 
});

app.get('/', (req, res) => {
    res.send(`<h1>🚀 Hiroshima Server is Online</h1><p>Active Subscribers: ${subscribers.size}</p>`);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
