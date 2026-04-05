const express = require('express');
const app = express();
app.use(express.json());

let lastTrade = {}; // تخزين آخر صفقة

// الباب الخاص بالماستر للإرسال
app.post('/trade', (req, res) => {
    lastTrade = req.body;
    console.log("استلمت صفقة من الماستر:", lastTrade);
    res.status(200).send("OK");
});

// الباب الخاص بالسلف للاستلام
app.get('/copy', (req, res) => {
    if (Object.keys(lastTrade).length === 0) {
        res.status(200).json({ message: "No trades available" });
    } else {
        res.status(200).json(lastTrade);
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
