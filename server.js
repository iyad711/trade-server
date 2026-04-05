const express = require('express');
const app = express();
app.use(express.json());

let lastTrade = {}; // تخزين آخر صفقة مستلمة

// 1. استقبال البيانات من الماستر
app.post('/trade', (req, res) => {
    lastTrade = req.body;
    lastTrade.server_time = new Date().toLocaleString(); // إضافة وقت السيرفر
    console.log("✅ استلمت بيانات:", lastTrade);
    res.status(200).json({ status: "Success" });
});

// 2. عرض البيانات في المتصفح وإرسالها للسلف
app.get('/copy', (req, res) => {
    if (Object.keys(lastTrade).length === 0) {
        res.send("<h1>🛰️ السيرفر يعمل</h1><p>بانتظار أول صفقة من الماستر...</p>");
    } else {
        // عرض البيانات بشكل جميل في المتصفح
        res.json(lastTrade); 
    }
});

// المسار الرئيسي للتأكد أن السيرفر حي
app.get('/', (req, res) => {
    res.send("<h1>🚀 Trade Sync Server is Online</h1>");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server is running on port ${PORT}`));
