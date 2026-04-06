const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

let lastTrade = {}; 
// استخدام Set لضمان عدم تكرار المشتركين
let subscribers = new Set(["7308459367"]); 
let msgHistory = {}; 

const BOT_TOKEN = "8601737426:AAHZPEJTRu01qteY7dp24mwpN9A4zFLeMUY";

// --- 1. ميزة استقبال المشتركين الجدد تلقائياً ---
// يجب ضبط Webhook للبوت على هذا المسار لاحقاً أو استخدامه لاستقبال الرسائل
app.post('/webhook', (req, res) => {
    if (req.body.message) {
        const chatId = req.body.message.chat.id.toString();
        if (!subscribers.has(chatId)) {
            subscribers.add(chatId);
            console.log(`👤 مشترك جديد انضم: ${chatId}`);
            // إرسال رسالة ترحيب
            axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                chat_id: chatId,
                text: "✅ تم تفعيل اشتراكك في بوت هيروشيما 711 بنجاح! ستصلك التوصيات هنا فوراً."
            }).catch(e => console.log("Error sending welcome"));
        }
    }
    res.sendStatus(200);
});

// --- 2. استقبال الصفقات من MT5 وتوزيعها للجميع ---
app.post('/trade', async (req, res) => {
    lastTrade = req.body;
    lastTrade.server_time = new Date().toLocaleString();
    
    console.log(`📢 توزيع صفقة: ${lastTrade.action} لـ ${subscribers.size} مشترك.`);

    if (lastTrade.msg) {
        // تحويل الـ Set إلى مصفوفة للإرسال
        const currentSubscribers = Array.from(subscribers);
        
        for (let chatId of currentSubscribers) {
            try {
                let payload = {
                    chat_id: chatId,
                    text: lastTrade.msg,
                    parse_mode: "Markdown"
                };

                // ميزة الرد الذكي لكل مشترك
                if (lastTrade.action !== "ORDER_OPEN" && msgHistory[lastTrade.ticket] && msgHistory[lastTrade.ticket][chatId]) {
                    payload.reply_to_message_id = msgHistory[lastTrade.ticket][chatId];
                }

                const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, payload);

                // حفظ رقم الرسالة للدخول فقط
                if (lastTrade.action === "ORDER_OPEN") {
                    if (!msgHistory[lastTrade.ticket]) msgHistory[lastTrade.ticket] = {};
                    msgHistory[lastTrade.ticket][chatId] = response.data.result.message_id;
                }
            } catch (err) {
                console.error(`❌ فشل الإرسال للمشترك ${chatId}:`, err.message);
            }
        }
    }

    res.status(200).json({ status: "Success", sent_to: subscribers.size });
});

// --- 3. مسار النسخ للسلف (Slave) ---
app.get('/copy', (req, res) => {
    res.json(lastTrade);
});

app.get('/', (req, res) => {
    res.send(`<h1>🚀 Hiroshima Server is Active</h1><p>Subscribers: ${subscribers.size}</p>`);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
