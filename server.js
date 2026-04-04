// كود السيرفر المركزي - Node.js
const express = require('express');
const app = express();
app.use(express.json()); // للسماح بقراءة بيانات الصفقات القادمة من ميتاتريدر

let currentTrade = null; // متغير لتخزين أحدث صفقة مستلمة من الماستر

// 1. رابط استقبال الصفقة من الماستر (المتداول الرئيسي)
app.post('/publish', (req, res) => {
    currentTrade = req.body; 
    console.log("------------------------------------");
    console.log("تم استقبال صفقة جديدة من الماستر:");
    console.log("الرمز:", currentTrade.symbol);
    console.log("النوع:", currentTrade.type == 0 ? "شراء (Buy)" : "بيع (Sell)");
    console.log("الحجم:", currentTrade.vol);
    console.log("------------------------------------");
    
    res.status(200).send({ status: "Trade Received by Server" });
});

// 2. رابط إرسال الصفقة للتابعين (الذين ينسخون)
app.get('/copy', (req, res) => {
    if (currentTrade) {
        res.json(currentTrade);
    } else {
        res.status(404).send({ message: "No trades available" });
    }
});

// تشغيل السيرفر على المنفذ 3000
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`نظام النسخ يعمل الآن بنجاح على المنفذ: ${PORT}`);
    console.log("انتظار الصفقات من منصة الماستر...");
});