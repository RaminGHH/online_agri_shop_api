# 🌿 سبزینه — ساختار کامل API
## Django REST Framework + PostgreSQL

---

## 📁 ساختار پروژه

```
sabzineh/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/        # احراز هویت و کاربران
│   ├── products/        # محصولات و دسته‌بندی
│   ├── orders/          # سفارش‌ها و سبد خرید
│   ├── payments/        # پرداخت و درگاه
│   ├── blog/            # مقالات و بلاگ
│   ├── notifications/   # پیامک و ایمیل
│   └── analytics/       # آمار و گزارش
├── manage.py
└── requirements.txt
```

---

## 🔐 1. ACCOUNTS — احراز هویت و کاربران

### Base URL: `/api/v1/auth/`

```
POST   /register/              # ثبت‌نام با موبایل
POST   /verify-otp/            # تأیید کد OTP
POST   /login/                 # ورود با موبایل + رمز
POST   /login/otp/             # ورود با کد پیامکی
POST   /token/refresh/         # تمدید JWT Token
POST   /logout/                # خروج و blacklist کردن token
POST   /forgot-password/       # فراموشی رمز — ارسال OTP
POST   /reset-password/        # تغییر رمز با OTP
POST   /change-password/       # تغییر رمز (لاگین‌شده)
GET    /me/                    # اطلاعات کاربر لاگین‌شده
PUT    /me/update/             # ویرایش پروفایل
POST   /me/avatar/             # آپلود تصویر پروفایل
```

### Base URL: `/api/v1/addresses/`

```
GET    /                       # لیست آدرس‌های کاربر
POST   /                       # افزودن آدرس جدید
GET    /{id}/                  # جزئیات آدرس
PUT    /{id}/                  # ویرایش آدرس
DELETE /{id}/                  # حذف آدرس
PATCH  /{id}/set-default/      # تنظیم به عنوان پیش‌فرض
```

### Models:
```python
User:
  - phone (unique)
  - email
  - first_name, last_name
  - national_code
  - birth_date
  - avatar
  - is_verified
  - wallet_balance
  - role: (customer | admin | staff)
  - created_at

OTPCode:
  - phone
  - code
  - expires_at
  - is_used
  - purpose: (register | login | forgot_password)

Address:
  - user (FK)
  - title
  - receiver_name
  - receiver_phone
  - province
  - city
  - address
  - postal_code
  - is_default
```

---

## 📦 2. PRODUCTS — محصولات

### Base URL: `/api/v1/products/`

```
GET    /                       # لیست محصولات (فیلتر + مرتب‌سازی + صفحه‌بندی)
GET    /{slug}/                # جزئیات محصول
GET    /search/                # جستجوی پیشرفته

# Query Params برای لیست:
# ?category=slug
# ?brand=id
# ?min_price=100000&max_price=500000
# ?in_stock=true
# ?has_discount=true
# ?rating=4
# ?ordering=price | -price | created_at | -sales_count
# ?page=1&page_size=12
# ?q=کود هیومیک  (full-text search)
```

### Base URL: `/api/v1/categories/`

```
GET    /                       # لیست دسته‌بندی‌ها (درختی)
GET    /{slug}/                # جزئیات دسته + زیردسته‌ها
GET    /{slug}/products/       # محصولات یک دسته
```

### Base URL: `/api/v1/brands/`

```
GET    /                       # لیست برندها
GET    /{id}/products/         # محصولات یک برند
```

### Base URL: `/api/v1/reviews/`

```
GET    /products/{product_id}/ # نظرات یک محصول
POST   /products/{product_id}/ # ثبت نظر (نیاز به خرید قبلی)
PUT    /{id}/                  # ویرایش نظر خودم
DELETE /{id}/                  # حذف نظر خودم
POST   /{id}/like/             # لایک نظر
```

### Base URL: `/api/v1/wishlist/`

```
GET    /                       # لیست علاقه‌مندی‌ها
POST   /toggle/                # افزودن/حذف از علاقه‌مندی
        body: { product_id: int }
```

### Models:
```python
Category:
  - name
  - slug
  - parent (self FK - nullable)
  - image
  - icon
  - is_active
  - order

Brand:
  - name
  - slug
  - logo
  - description

Product:
  - name
  - slug
  - category (FK)
  - brand (FK)
  - description
  - short_description
  - price
  - compare_price (قیمت قبل از تخفیف)
  - cost_price (قیمت خرید - برای حسابداری)
  - stock
  - low_stock_threshold
  - sku
  - weight
  - unit: (kg | g | liter | piece | package)
  - is_active
  - is_featured
  - sales_count
  - views_count
  - meta_title, meta_description (سئو)
  - created_at, updated_at

ProductImage:
  - product (FK)
  - image
  - alt_text
  - order
  - is_main

ProductAttribute:
  - product (FK)
  - key (مثلاً: درصد هیومیک)
  - value (مثلاً: ۷۰٪)
  - order

Review:
  - product (FK)
  - user (FK)
  - rating (1-5)
  - title
  - body
  - is_approved
  - is_verified_purchase
  - likes_count
  - created_at
```

---

## 🛒 3. ORDERS — سبد خرید و سفارش‌ها

### Base URL: `/api/v1/cart/`

```
GET    /                       # سبد خرید فعلی
POST   /items/                 # افزودن به سبد
        body: { product_id, quantity, unit }
PUT    /items/{id}/            # تغییر تعداد
DELETE /items/{id}/            # حذف از سبد
DELETE /clear/                 # خالی کردن سبد
POST   /apply-coupon/          # اعمال کد تخفیف
        body: { code: string }
DELETE /remove-coupon/         # حذف کوپن
GET    /summary/               # خلاصه و محاسبه قیمت نهایی
```

### Base URL: `/api/v1/orders/`

```
GET    /                       # لیست سفارش‌های من
POST   /                       # ثبت سفارش از سبد
        body: { address_id, shipping_method, payment_method, note }
GET    /{id}/                  # جزئیات سفارش
GET    /{id}/tracking/         # پیگیری سفارش
POST   /{id}/cancel/           # لغو سفارش
POST   /{id}/return/           # درخواست مرجوعی
```

### Base URL: `/api/v1/shipping/`

```
GET    /methods/               # روش‌های ارسال موجود
POST   /calculate/             # محاسبه هزینه ارسال
        body: { address_id, cart_weight }
```

### Models:
```python
Cart:
  - user (FK - nullable برای guest)
  - session_key (برای guest)
  - coupon (FK - nullable)
  - created_at, updated_at

CartItem:
  - cart (FK)
  - product (FK)
  - quantity
  - unit

Coupon:
  - code (unique)
  - type: (percent | fixed)
  - value
  - min_order_amount
  - max_discount_amount
  - usage_limit
  - used_count
  - user_usage_limit (هر کاربر چند بار)
  - is_active
  - expires_at

Order:
  - user (FK)
  - order_number (unique, auto-generated)
  - address (snapshot of address)
  - shipping_method
  - shipping_cost
  - coupon (FK - nullable)
  - discount_amount
  - items_total
  - total_amount
  - payment_method
  - payment_status: (pending | paid | failed | refunded)
  - status: (pending | processing | shipped | delivered | cancelled | returned)
  - tracking_code
  - carrier
  - note
  - paid_at
  - shipped_at
  - delivered_at
  - created_at

OrderItem:
  - order (FK)
  - product (FK)
  - product_name (snapshot)
  - product_sku (snapshot)
  - quantity
  - unit
  - unit_price (snapshot)
  - total_price

OrderStatusHistory:
  - order (FK)
  - status
  - description
  - changed_by (FK User)
  - created_at

ShippingMethod:
  - name
  - carrier
  - estimated_days
  - base_cost
  - free_shipping_threshold
  - is_active
```

---

## 💳 4. PAYMENTS — پرداخت

### Base URL: `/api/v1/payments/`

```
POST   /initiate/              # شروع پرداخت و دریافت URL درگاه
        body: { order_id, gateway: (zarinpal | mellat) }
GET    /verify/                # تأیید پرداخت (callback از درگاه)
        query: ?Authority=...&Status=OK
GET    /transactions/          # تاریخچه تراکنش‌های من
GET    /transactions/{id}/     # جزئیات تراکنش

# کیف پول
GET    /wallet/                # موجودی کیف پول
POST   /wallet/charge/         # شارژ کیف پول
GET    /wallet/transactions/   # تاریخچه کیف پول
```

### Models:
```python
Transaction:
  - user (FK)
  - order (FK - nullable)
  - transaction_id (از درگاه)
  - authority (زرین‌پال)
  - gateway: (zarinpal | mellat | wallet)
  - amount
  - status: (pending | success | failed | refunded)
  - gateway_response (JSON)
  - created_at

WalletTransaction:
  - user (FK)
  - type: (charge | spend | refund)
  - amount
  - balance_after
  - description
  - reference (FK Transaction - nullable)
  - created_at
```

---

## 📝 5. BLOG — مقالات

### Base URL: `/api/v1/blog/`

```
GET    /posts/                 # لیست مقالات
        query: ?category=slug&tag=name&q=search&page=1
GET    /posts/{slug}/          # جزئیات مقاله
GET    /posts/{slug}/related/  # مقالات مرتبط
GET    /categories/            # دسته‌بندی مقالات
GET    /tags/                  # تگ‌ها
POST   /posts/{slug}/view/     # ثبت بازدید
```

### Models:
```python
BlogCategory:
  - name, slug, description

Post:
  - title, slug
  - category (FK)
  - author (FK User)
  - cover_image
  - excerpt
  - body (rich text)
  - tags (M2M)
  - status: (draft | published)
  - views_count
  - read_time (minutes)
  - meta_title, meta_description
  - published_at, created_at

Tag:
  - name, slug
```

---

## 🔔 6. NOTIFICATIONS

### Base URL: `/api/v1/notifications/`

```
GET    /                       # لیست اعلان‌های من
PATCH  /{id}/read/             # خواندن اعلان
PATCH  /read-all/              # خواندن همه
DELETE /{id}/                  # حذف اعلان

# تنظیمات
GET    /settings/              # تنظیمات اطلاع‌رسانی
PUT    /settings/              # ویرایش تنظیمات
```

---

## 👑 7. ADMIN — پنل مدیریت

### Base URL: `/api/v1/admin/`

> همه endpoint‌ها نیاز به `role=admin` دارن

```
# داشبورد
GET    /dashboard/stats/       # آمار کلی
GET    /dashboard/sales-chart/ # نمودار فروش
        query: ?period=daily|weekly|monthly
GET    /dashboard/recent-orders/
GET    /dashboard/low-stock/
GET    /dashboard/top-products/

# محصولات
GET    /products/              # لیست + فیلتر
POST   /products/              # ایجاد محصول
GET    /products/{id}/         # جزئیات
PUT    /products/{id}/         # ویرایش
DELETE /products/{id}/         # حذف
PATCH  /products/{id}/toggle/  # فعال/غیرفعال
POST   /products/{id}/images/  # آپلود تصویر
DELETE /products/images/{id}/  # حذف تصویر
POST   /products/bulk-delete/  # حذف گروهی
PATCH  /products/bulk-status/  # تغییر وضعیت گروهی

# دسته‌بندی
GET    /categories/
POST   /categories/
PUT    /categories/{id}/
DELETE /categories/{id}/

# سفارش‌ها
GET    /orders/                # لیست + فیلتر
        query: ?status=pending&from_date=&to_date=&user_id=
GET    /orders/{id}/           # جزئیات
PATCH  /orders/{id}/status/    # تغییر وضعیت
        body: { status, description, tracking_code }
GET    /orders/export/         # خروجی اکسل

# کاربران
GET    /users/
GET    /users/{id}/
PATCH  /users/{id}/role/
PATCH  /users/{id}/block/
GET    /users/{id}/orders/

# کوپن‌ها
GET    /coupons/
POST   /coupons/
PUT    /coupons/{id}/
DELETE /coupons/{id}/
GET    /coupons/{id}/usage/    # گزارش استفاده

# نظرات
GET    /reviews/               # نظرات منتظر تأیید
PATCH  /reviews/{id}/approve/
DELETE /reviews/{id}/

# بلاگ
GET    /blog/posts/
POST   /blog/posts/
PUT    /blog/posts/{id}/
DELETE /blog/posts/{id}/
PATCH  /blog/posts/{id}/publish/

# گزارش‌ها
GET    /reports/sales/         # گزارش فروش
GET    /reports/products/      # گزارش محصولات
GET    /reports/users/         # گزارش کاربران
GET    /reports/export/        # خروجی اکسل/PDF
```

---

## 🗺️ URL Configuration کلی

```python
# config/urls.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('auth/',          include('apps.accounts.urls.auth')),
        path('addresses/',     include('apps.accounts.urls.addresses')),
        path('products/',      include('apps.products.urls.products')),
        path('categories/',    include('apps.products.urls.categories')),
        path('brands/',        include('apps.products.urls.brands')),
        path('reviews/',       include('apps.products.urls.reviews')),
        path('wishlist/',      include('apps.products.urls.wishlist')),
        path('cart/',          include('apps.orders.urls.cart')),
        path('orders/',        include('apps.orders.urls.orders')),
        path('shipping/',      include('apps.orders.urls.shipping')),
        path('payments/',      include('apps.payments.urls')),
        path('blog/',          include('apps.blog.urls')),
        path('notifications/', include('apps.notifications.urls')),
        path('admin/',         include('apps.accounts.urls.admin')),
    ])),
    # Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(), name='swagger'),
]
```

---

## 🔑 Authentication Flow

```
1. POST /auth/register/     → ارسال OTP
2. POST /auth/verify-otp/   → تأیید و دریافت { access, refresh }
3. Header: Authorization: Bearer <access_token>
4. POST /auth/token/refresh/ → تمدید با refresh token
```

---

## 📌 نکات فنی مهم

```
Pagination:   PageNumberPagination — page_size=12
Filtering:    django-filter
Search:       SearchFilter روی name, description
Ordering:     OrderingFilter
Permissions:  IsAuthenticated | IsAdminUser | IsOwnerOrAdmin
Throttling:   OTP: 3/hour | Login: 10/min | General: 100/min
Image Upload: Pillow + compress قبل از ذخیره
Async Tasks:  Celery برای ارسال SMS و Email
Cache:        Redis — cache لیست محصولات و دسته‌بندی
```

---

## 📊 خلاصه تعداد Endpoints

| App | تعداد |
|---|---|
| Accounts | ۱۸ |
| Products | ۱۶ |
| Orders | ۱۴ |
| Payments | ۷ |
| Blog | ۶ |
| Notifications | ۶ |
| Admin | ۳۸ |
| **جمع** | **~۱۰۵** |
