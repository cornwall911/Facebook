# Facebook Viral Scout (Powered by Scrapling) 🚀

أداة آلية ذكية متخصصة في سحب وتحليل منشورات فيسبوك الفايرال (+100 تفاعل) من الجروبات الخاصة والعامة، واستخراج صور المشترين الحقيقية والنصوص، وتصديرها في ملف Excel وداش بورد تفاعلية بنقرة زر.

مبنية بالكامل على محرك **Scrapling** لـ D4Vinci المعتمد على **Patchright** لتخطي كشف البوتات والـ Fingerprinting.

---

## 🌟 المميزات الرئيسية
* **تخفي فائق (Stealthy Scraping):** لا يتم كشف المتصفح كبوت، ويعمل في الخلفية (Headless) دون إزعاج.
* **فلترة دقيقة (+100 تفاعل):** يتجاهل تلقائياً المنشورات الضعيفة، ويركز على المنشورات التي أثبتت نجاحها (Viral Proof).
* **سحب الكابشن كاملاً:** يضغط تلقائياً على "See more / عرض المزيد" لقراءة المنشور كاملاً.
* **تحميل صور عالية الدقة:** حفظ صور المستخدمين الحقيقية في مجلدات منظمة باسم كل منتج ورقم البوست.
* **مخرجات فورية متعددة:**
  1. **ملف Excel (`viral_posts.xlsx`):** يحتوي على الروابط والتفاعلات والكومنتات والشير والنص بالكامل.
  2. **قاعدة بيانات JSON (`viral_posts.json`):** داتا مهيكلة للأتمتة.
  3. **لوحة تحكم تفاعلية (`dashboard.html`):** تفتح في المتصفح لاستعراض البوستات ككروت ونسخ الكابشن بنقرة واحدة (1-Click Copy).
* **دعم التشغيل السحابي عبر GitHub Actions:** جدول يومي وتنزيل المخرجات كـ Artifacts بضغطة زر.

---

## 📁 هيكل المشروع

```
e:\work\
├── fb_winner_scout/
│   ├── config.py         # الإعدادات والكوكيز
│   ├── session.py        # جلسة المتصفح الخفية (Patchright)
│   ├── crawler.py        # السكرول والبحث في الجروبات
│   ├── parser.py         # تحليل الأرقام والنصوص
│   ├── storage.py        # حفظ Excel و JSON وتنزيل الصور
│   ├── dashboard.py      # توليد الداش بورد البصرية HTML
│   └── pipeline.py       # تنسيق وإدارة مراحل البحث
├── .github/workflows/
│   └── fb-scout.yml      # أتمتة سحابية على GitHub Actions
├── data/
│   ├── images/           # الصور المحملة لكل بوست
│   └── reports/          # تقارير Excel و Dashboard HTML
├── cookies.json          # كوكيز حساب فيسبوك (الحساب المخصص)
├── groups.txt            # قائمة الجروبات المستهدفة
├── keywords.txt          # قائمة الكلمات المفتاحية
├── run_scout.bat         # تشغيل فوري بنقرة واحدة للويندوز
└── README.md
```

---

## 🚀 طريقة التشغيل المحلي (على جهازك)

### 1. تجهيز الكوكيز:
* ثبت إضافة [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) على متصفحك.
* افتح حساب فيسبوك المخصص، واضغط على الإضافة واختر **Export -> Export as JSON**.
* احفظ الملف باسم `cookies.json` في مجلد `e:\work\`.

### 2. تجهيز الجروبات والكلمات المفتاحية:
* انسخ `groups.example.txt` إلى `groups.txt` وضع روابط الجروبات أو أرقام الـ IDs.
* انسخ `keywords.example.txt` إلى `keywords.txt` وضع المنتجات أو الكلمات المطلوب البحث عنها.

### 3. التشغيل:
ببساطة اضغط مرتين على ملف **`run_scout.bat`**  
أو عبر التيرمينال:
```bash
python -m fb_winner_scout run --headless
```

---

## ☁️ طريقة التشغيل عبر GitHub Actions

1. ارفع المشروع على مستودع GitHub (Private).
2. ادخل على **Settings > Secrets and variables > Actions > Secrets**:
   * أضف Secret باسم `FB_COOKIES_JSON` وضع بداخله محتوى ملف `cookies.json`.
   * (اختياري) أضف `PROXY_URL` إذا أردت استخدام بروكسي سكني.
3. ادخل على تبويب **Actions**، اختر **Facebook Viral Posts Scout**، ثم اضغط **Run workflow**.
4. بعد انتهاء التشغيل، ستجد ملفات الـ Excel والصور والداش بورد مرفوعة في قسم **Artifacts** جاهزة للتنزيل كملف مضغوط!
