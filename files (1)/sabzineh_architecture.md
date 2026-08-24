# سبزینه — معماری جامع و قابل توسعه
## طراحی برای امروز، آماده برای فردا

---

## 1. فلسفه طراحی

> **اشتباه رایج:** ساختن یک فروشگاه کشاورزی که بعداً بخواهیم موبایل هم بهش اضافه کنیم.
> **رویکرد درست:** ساختن یک **پلتفرم تجارت الکترونیک** که اولین مصرف‌کننده‌اش فروشگاه کشاورزی است.

تفاوت این دو رویکرد در لایه **دیتابیس** و **API** است، نه در UI.
UI می‌تواند فردا عوض شود. دیتابیس بد طراحی شده، هزینه بازطراحی سنگینی دارد.

---

## 2. آنچه نباید در مدل‌ها هاردکد شود

### ❌ اشتباه — Category هاردکد شده برای کشاورزی:
```python
# این رویکرد فقط برای کشاورزی کار می‌کند
class Category(models.Model):
    name = models.CharField(max_length=100)
    # هیچ ساختار درختی ندارد، قابل توسعه نیست
```

### ✅ درست — Category درختی نامحدود:
```python
class Category(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    parent      = models.ForeignKey(
                    'self', null=True, blank=True,
                    related_name='children',
                    on_delete=models.SET_NULL
                  )
    # می‌تواند تا هر عمقی ادامه داشته باشد:
    # الکترونیک → موبایل → آیفون → آیفون ۱۶
    # کشاورزی → کود → کود آلی → هیومیک اسید
```

---

## 3. مدل Product — قلب سیستم

مهم‌ترین تصمیم معماری است. Product باید برای هر نوع کالایی کار کند.

```python
class Product(models.Model):

    # ── اطلاعات پایه (برای همه نوع محصول یکسان) ──
    name              = models.CharField(max_length=255)
    slug              = models.SlugField(unique=True)
    category          = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand             = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    description       = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)

    # ── قیمت‌گذاری ──
    price             = models.DecimalField(max_digits=12, decimal_places=0)
    compare_price     = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    cost_price        = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    # ── موجودی ──
    stock             = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    sku               = models.CharField(max_length=100, unique=True)
    weight            = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # ── وضعیت ──
    is_active         = models.BooleanField(default=True)
    is_featured       = models.BooleanField(default=False)

    # ── آمار ──
    views_count       = models.IntegerField(default=0)
    sales_count       = models.IntegerField(default=0)

    # ── سئو ──
    meta_title        = models.CharField(max_length=60, blank=True)
    meta_description  = models.CharField(max_length=160, blank=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)


# ── کلید طلایی: Attribute های داینامیک ──
# این جدول است که Product را برای هر حوزه‌ای قابل استفاده می‌کند
class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, related_name='attributes', on_delete=models.CASCADE)
    key     = models.CharField(max_length=100)   # "RAM" یا "درصد هیومیک"
    value   = models.CharField(max_length=500)   # "8GB" یا "70%"
    order   = models.IntegerField(default=0)
    # هیچ چیز هاردکد نشده — هر حوزه مشخصات خودش را دارد


# ── Variant: وریانت محصول (سایز، رنگ، ظرفیت) ──
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name    = models.CharField(max_length=100)   # "آبی ۱۲۸GB" یا "بسته ۵ کیلویی"
    sku     = models.CharField(max_length=100, unique=True)
    price   = models.DecimalField(max_digits=12, decimal_places=0)
    stock   = models.IntegerField(default=0)
    # این مدل اجازه می‌دهد:
    # موبایل: رنگ‌های مختلف، حافظه‌های مختلف
    # کود: وزن‌های مختلف (1kg, 5kg, 25kg)
    # لوازم خانگی: ولتاژ، رنگ
```

---

## 4. سناریوهای مختلف — چطور همه را هندل می‌کند

### سناریو A: فروشگاه کشاورزی (الان)
```
Category: کود → کود آلی → هیومیک اسید
Product Attributes:
  - درصد هیومیک: 70%
  - روش مصرف: محلول‌پاشی
  - وزن: 1 کیلوگرم
ProductVariant:
  - بسته 1 کیلویی — 185,000 تومان
  - بسته 5 کیلویی — 780,000 تومان
  - بسته 25 کیلویی — 3,200,000 تومان
```

### سناریو B: موبایل (فردا)
```
Category: دیجیتال → موبایل → آیفون
Product Attributes:
  - پردازنده: A18 Pro
  - دوربین اصلی: 48MP
  - شبکه: 5G
ProductVariant:
  - آبی / 128GB — 65,000,000 تومان
  - مشکی / 256GB — 72,000,000 تومان
  - تیتانیوم / 512GB — 88,000,000 تومان
```

### سناریو C: لوازم خانگی (پس‌فردا)
```
Category: خانه → لوازم آشپزخانه → یخچال
Product Attributes:
  - حجم: 450 لیتر
  - سیستم: No-Frost
  - ولتاژ: 220V
ProductVariant:
  - رنگ نقره‌ای — 42,000,000 تومان
  - رنگ مشکی — 43,500,000 تومان
```

**نتیجه:** همان کد، همان API، همان پنل ادمین — فقط دسته‌بندی و Attribute عوض می‌شود.

---

## 5. فرآیندهای عملیاتی (Business Processes)

### فرآیند 1: ثبت سفارش تا تحویل

```
کاربر محصول انتخاب می‌کند
        ↓
افزودن به سبد (Cart)
  [Redis Cache برای سرعت]
        ↓
تکمیل خرید (Checkout)
  - انتخاب آدرس
  - انتخاب روش ارسال + محاسبه هزینه
  - اعمال کوپن
  - محاسبه نهایی
        ↓
پرداخت آنلاین
  [Zarinpal / Mellat]
        ↓
تأیید پرداخت (Webhook از درگاه)
  - ثبت Transaction
  - کاهش موجودی Product
  - ارسال SMS تأیید به مشتری
  - اطلاع‌رسانی به ادمین
        ↓
پردازش توسط انبار (Processing)
  - بسته‌بندی
  - تحویل به شرکت حمل
        ↓
ارسال (Shipped)
  - ثبت کد رهگیری
  - ارسال SMS با کد رهگیری
        ↓
تحویل (Delivered)
  - تأیید دریافت توسط مشتری یا سیستم
  - امکان ثبت نظر فعال می‌شود
```

### فرآیند 2: لغو و مرجوعی

```
مشتری درخواست لغو/مرجوعی می‌دهد
        ↓
بررسی شرایط:
  - لغو قبل از ارسال: خودکار
  - مرجوعی بعد از تحویل: 7 روز مهلت
        ↓
تأیید ادمین
        ↓
بازگشت وجه:
  - به کیف پول داخلی (فوری)
  - یا به حساب بانکی (3-5 روز کاری)
        ↓
افزایش موجودی محصول
```

### فرآیند 3: مدیریت موجودی

```
فروش محصول
        ↓
کاهش stock در Product
        ↓
آیا stock <= low_stock_threshold؟
  بله → ارسال اعلان به ادمین
        → نمایش "موجودی کم" در سایت
  خیر → ادامه عادی
        ↓
آیا stock == 0؟
  بله → نمایش "ناموجود"
        → دکمه "اطلاع‌رسانی هنگام موجود شدن"
```

### فرآیند 4: سیستم نظردهی

```
مشتری سفارش را تحویل گرفت
        ↓
بررسی: آیا این کاربر این محصول را خریده؟
  [is_verified_purchase = True]
        ↓
ثبت نظر (Rating + متن)
        ↓
در انتظار تأیید ادمین
        ↓
تأیید → نمایش در سایت + به‌روزرسانی میانگین امتیاز
رد → اطلاع به کاربر
```

---

## 6. ساختار دیتابیس — جداول اصلی

```
┌─────────────────────────────────────────────────────────────┐
│                      USER                                    │
│  id | phone | email | role | wallet_balance | is_verified   │
└──────────────────┬──────────────────────────────────────────┘
                   │ 1:N
    ┌──────────────┼──────────────┐
    ↓              ↓              ↓
 ADDRESS         ORDER         REVIEW
    │              │
    │         1:N  │  1:N
    │        ┌─────┘
    │        ↓
    │    ORDER_ITEM ────→ PRODUCT
    │        │                │
    │        │           1:N  │  1:N
    │    TRANSACTION     ┌────┴────┐
    │                    ↓        ↓
    │            PRODUCT_IMAGE  PRODUCT_ATTRIBUTE
    │
    └── ADDRESS ──→ ORDER (snapshot آدرس در لحظه خرید)


PRODUCT ────→ CATEGORY (درختی، self-referential)
PRODUCT ────→ BRAND
PRODUCT ────→ PRODUCT_VARIANT (رنگ، سایز، ظرفیت)

ORDER ──────→ COUPON
ORDER ──────→ SHIPPING_METHOD
ORDER ──────→ ORDER_STATUS_HISTORY (timeline)
```

---

## 7. تصمیمات فنی کلیدی

### 7.1 چرا Attribute داینامیک (EAV) به جای جداول جداگانه؟

| رویکرد | مزیت | معایب |
|---|---|---|
| جدول جداگانه برای هر نوع کالا | Query سریع‌تر | برای هر حوزه جدید باید migration جدید زد |
| EAV (کلید-مقدار داینامیک) | بی‌نهایت قابل توسعه | Query کمی پیچیده‌تر |
| JSON Field | انعطاف کامل | جستجو و فیلتر سخت‌تر |

**توصیه برای این پروژه:** ترکیب EAV + JSON:
- مشخصات اصلی (برای فیلتر): EAV در جدول ProductAttribute
- مشخصات کامل (برای نمایش): JSONField در Product

```python
class Product(models.Model):
    # ...
    specs_json = models.JSONField(default=dict, blank=True)
    # {"RAM": "8GB", "Display": "6.1 inch", "Battery": "3279 mAh"}
```

### 7.2 Snapshot در سفارش — خیلی مهم

```python
class OrderItem(models.Model):
    order         = models.ForeignKey(Order, on_delete=models.CASCADE)
    product       = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    # ── Snapshot اطلاعات محصول در لحظه خرید ──
    product_name  = models.CharField(max_length=255)  # اگر نام محصول عوض شد، سفارش قدیمی درست بماند
    product_sku   = models.CharField(max_length=100)
    unit_price    = models.DecimalField(max_digits=12, decimal_places=0)  # قیمت لحظه خرید
    quantity      = models.IntegerField()
    # ──────────────────────────────────────────

    @property
    def total_price(self):
        return self.unit_price * self.quantity
```

### 7.3 Multi-tenant آماده شدن (اگر بخواهی SaaS بسازی)

```python
# اگر فردا بخواهی چند فروشگاه روی یک سیستم داشته باشی:
class Store(models.Model):
    name   = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, unique=True)
    owner  = models.ForeignKey(User, on_delete=models.CASCADE)
    plan   = models.CharField(choices=[('basic','Basic'),('pro','Pro')], max_length=20)

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # اضافه می‌شود
    # بقیه فیلدها...

# با این یک فیلد، کل سیستم Multi-tenant می‌شود
# هر فروشگاه محصولات، سفارشات و مشتریان جداگانه دارد
```

---

## 8. API Design — نکات حیاتی

### 8.1 Versioning از همان اول

```python
# ✅ درست — همیشه با نسخه شروع کن
urlpatterns = [
    path('api/v1/', include('apps.api.v1.urls')),
    # فردا می‌توانی v2 اضافه کنی بدون شکستن v1
]

# ❌ اشتباه
urlpatterns = [
    path('api/', include('apps.api.urls')),
]
```

### 8.2 Response Format یکسان برای همه endpoint ها

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 12,
    "total": 1408
  },
  "error": null
}
```

### 8.3 Permission لایه‌بندی شده

```python
# 3 لایه permission داریم:
# 1. Public — هرکسی می‌تواند ببیند
# 2. IsAuthenticated — فقط کاربر لاگین
# 3. IsAdminUser — فقط ادمین

class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]  # لیست محصولات عمومی است

class OrderCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]  # خرید نیاز به لاگین دارد

class AdminProductView(generics.ModelViewSet):
    permission_classes = [IsAdminUser]  # مدیریت فقط برای ادمین
```

---

## 9. مسیر توسعه پیشنهادی

### فاز 1 — MVP (ماه 1-2)
```
✅ مدل‌های پایه (User, Product, Category, Order, Transaction)
✅ API احراز هویت (OTP + JWT)
✅ API محصولات (لیست، جزئیات، جستجو)
✅ API سبد خرید
✅ API سفارش + پرداخت (زرین‌پال)
✅ پنل ادمین پایه (محصولات + سفارش‌ها)
```

### فاز 2 — تکمیل (ماه 3)
```
⬜ ProductVariant (وریانت‌ها)
⬜ سیستم نظرات
⬜ کوپن و تخفیف
⬜ کیف پول داخلی
⬜ گزارش‌های مالی
⬜ سیستم پیامک
```

### فاز 3 — توسعه (ماه 4-6)
```
⬜ جستجوی پیشرفته (Elasticsearch)
⬜ سیستم وفاداری (امتیاز و پاداش)
⬜ اپلیکیشن موبایل (React Native)
⬜ اضافه کردن دسته‌بندی جدید (مثلاً لوازم خانگی)
⬜ تبدیل به SaaS (Multi-tenant)
```

---

## 10. چک‌لیست قبل از شروع کدنویسی

قبل از اینکه یک خط کد بزنی، این‌ها را یک بار مرور کن:

- [ ] **آیا Category درختی نامحدود است؟** (self-referential FK)
- [ ] **آیا ProductAttribute داینامیک است؟** (EAV — نه فیلد ثابت)
- [ ] **آیا ProductVariant وجود دارد؟** (رنگ، سایز، ظرفیت)
- [ ] **آیا OrderItem snapshot می‌گیرد؟** (نام و قیمت لحظه خرید)
- [ ] **آیا API نسخه‌بندی دارد؟** (/api/v1/)
- [ ] **آیا select_related از روز اول استفاده می‌شود؟** (جلوگیری از N+1)
- [ ] **آیا Store فیلد آماده است؟** (برای آینده Multi-tenant)
- [ ] **آیا soft delete استفاده می‌شود؟** (is_deleted به جای حذف واقعی)

---

## 11. جمع‌بندی

**با این معماری:**

| سناریو | کار مورد نیاز |
|---|---|
| اضافه کردن دسته "موبایل" | فقط یک Category جدید در دیتابیس |
| اضافه کردن "رنگ" به محصول | یک ProductVariant جدید |
| اضافه کردن مشخصه "رم" | یک ProductAttribute جدید |
| راه‌اندازی فروشگاه دوم | اضافه کردن فیلد Store به مدل‌ها |
| تبدیل به SaaS | پیاده‌سازی Multi-tenant روی همان مدل‌ها |

**هیچ‌کدام از این‌ها نیاز به بازنویسی ندارند** — اگر از همان اول درست طراحی شده باشد.

---

*مستند طراحی فروشگاه سبزینه — نسخه 1.0*
*آماده برای کشاورزی، آماده برای موبایل، آماده برای هر چیز دیگری*
