const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

let lastTrade = {}; 
let subscribers = new Set(["7308459367"]); // رقمك مضاف تلقائياً
let msgHistory = {}; 
const BOT_TOKEN = "8601737426:AAHZPEJTRu01qteY7dp24mwpN9A4zFLeMUY";

// --- 1. استقبال المشتركين الجدد ---
app.post('/webhook', (req, res) => {
    if (req.body && req.body.message) {
        const chatId = req.body.message.chat.id.toString();
        subscribers.add(chatId);
        console.log(`👤 مشترك جديد: ${chatId}`);
    }
    res.sendStatus(200);
});

// --- 2. استقبال الصفقة من الماستر وتوزيعها ---
app.post('/trade', async (req, res) => {
    lastTrade = req.body; // حفظ الصفقة فوراً للنسخ (Slave)
    lastTrade.server_time = new Date().toISOString();
    
    console.log("⚡ إشارة جديدة من الماستر:", lastTrade.action);

    if (lastTrade.msg) {
        const userList = Array.from(subscribers);
        for (let chatId of userList) {
            try {
                let payload = { chat_id: chatId, text: lastTrade.msg, parse_mode: "Markdown" };
                // ميزة الرد (Reply) لكل مشترك
                if (lastTrade.action !== "ORDER_OPEN" && msgHistory[lastTrade.ticket] && msgHistory[lastTrade.ticket][chatId]) {
                    payload.reply_to_message_id = msgHistory[lastTrade.ticket][chatId];
                }
                const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, payload);
                if (lastTrade.action === "ORDER_OPEN") {
                    if (!msgHistory[lastTrade.ticket]) msgHistory[lastTrade.ticket] = {};
                    msgHistory[lastTrade.ticket][chatId] = response.data.result.message_id;
                }
            } catch (e) { console.error("Error for:", chatId); }
        }
    }
    res.status(200).json({ status: "Success" });
});

// --- 3. نقطة النسخ للسلف (Slave) ---
app.get('/copy', (req, res) => {
    res.json(lastTrade); 
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("Hiroshima Server Online"));
