const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

// الذاكرة المؤقتة
let lastTrade = {}; 
let subscribers = new Set(["7308459367"]); 
let msgHistory = {}; 

const BOT_TOKEN = "8601737426:AAHZPEJTRu01qteY7dp24mwpN9A4zFLeMUY";

// 1. استقبال المشتركين
app.post('/webhook', (req, res) => {
    if (req.body && req.body.message) {
        const chatId = req.body.message.chat.id.toString();
        if (!subscribers.has(chatId)) {
            subscribers.add(chatId);
            axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                chat_id: chatId,
                text: "✅ تم تفعيل اشتراكك في Hiroshima 711!"
            }).catch(e => console.log("Error welcome"));
        }
    }
    res.sendStatus(200);
});

// 2. استقبال وتوزيع الصفقات (الرد الذكي والنسخ)
app.post('/trade', async (req, res) => {
    try {
        lastTrade = req.body;
        lastTrade.server_time = new Date().toLocaleString();
        
        console.log("✅ استلمت بيانات:", lastTrade.action);

        if (lastTrade.msg) {
            const currentSubscribers = Array.from(subscribers);
            for (let chatId of currentSubscribers) {
                let payload = {
                    chat_id: chatId,
                    text: lastTrade.msg,
                    parse_mode: "Markdown"
                };

                // ميزة الرد (Reply) على نفس الرسالة
                if (lastTrade.action !== "ORDER_OPEN" && msgHistory[lastTrade.ticket] && msgHistory[lastTrade.ticket][chatId]) {
                    payload.reply_to_message_id = msgHistory[lastTrade.ticket][chatId];
                }

                const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, payload);

                // حفظ رقم الرسالة للأصل (ORDER_OPEN)
                if (lastTrade.action === "ORDER_OPEN") {
                    if (!msgHistory[lastTrade.ticket]) msgHistory[lastTrade.ticket] = {};
                    msgHistory[lastTrade.ticket][chatId] = response.data.result.message_id;
                }
            }
        }
        res.status(200).json({ status: "Success" });
    } catch (error) {
        console.error("Error in /trade:", error.message);
        res.status(500).json({ status: "Error" });
    }
});

// 3. مسار النسخ (للسليف)
app.get('/copy', (req, res) => {
    res.json(lastTrade); 
});

app.get('/', (req, res) => {
    res.send(`<h1>🚀 Hiroshima Server is Online</h1><p>Subscribers: ${subscribers.size}</p>`);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
