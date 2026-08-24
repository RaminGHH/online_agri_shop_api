"""
=============================================
  سبزینه — models.py
  App: orders
  جداول: ShippingMethod, Coupon, CouponUsage,
         Cart, CartItem, Order, OrderItem,
         OrderStatusHistory
=============================================
"""

import uuid
import random
import string
from django.db import models
from django.utils import timezone
from apps.accounts.models import User, Address
from apps.products.models import Product, ProductVariant


# ─────────────────────────────────────────
#  SHIPPING METHOD
# ─────────────────────────────────────────
class ShippingMethod(models.Model):
    id                      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name                    = models.CharField(max_length=100, verbose_name='نام')
    carrier                 = models.CharField(max_length=50, verbose_name='شرکت حمل')  # پست / تیپاکس / پیک
    estimated_days_min      = models.PositiveIntegerField(default=1, verbose_name='حداقل روز')
    estimated_days_max      = models.PositiveIntegerField(default=3, verbose_name='حداکثر روز')
    base_cost               = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='هزینه پایه')
    free_shipping_threshold = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='حداقل خرید ارسال رایگان')
    is_active               = models.BooleanField(default=True)
    order                   = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'shipping_methods'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.carrier})"

    def get_cost(self, order_amount):
        if self.free_shipping_threshold and order_amount >= self.free_shipping_threshold:
            return 0
        return self.base_cost


# ─────────────────────────────────────────
#  COUPON
# ─────────────────────────────────────────
class Coupon(models.Model):

    class Type(models.TextChoices):
        PERCENT = 'percent', 'درصدی'
        FIXED   = 'fixed',   'مقدار ثابت'

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code                = models.CharField(max_length=50, unique=True, verbose_name='کد تخفیف')
    type                = models.CharField(max_length=10, choices=Type.choices, verbose_name='نوع')
    value               = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='مقدار')
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='سقف تخفیف')
    min_order_amount    = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='حداقل خرید')
    usage_limit         = models.PositiveIntegerField(null=True, blank=True, verbose_name='حداکثر استفاده کل')
    user_usage_limit    = models.PositiveIntegerField(default=1, verbose_name='حداکثر استفاده هر کاربر')
    used_count          = models.PositiveIntegerField(default=0, verbose_name='تعداد استفاده')
    is_active           = models.BooleanField(default=True)
    starts_at           = models.DateTimeField(null=True, blank=True, verbose_name='شروع')
    expires_at          = models.DateTimeField(null=True, blank=True, verbose_name='انقضا')
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'
        verbose_name = 'کوپن تخفیف'
        verbose_name_plural = 'کوپن‌های تخفیف'

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, amount):
        if self.type == self.Type.PERCENT:
            discount = amount * self.value / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = self.value
        return min(discount, amount)


class CouponUsage(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon     = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order      = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    amount     = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ تخفیف')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usages'


# ─────────────────────────────────────────
#  CART
# ─────────────────────────────────────────
class Cart(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # برای کاربر مهمان
    coupon     = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f"سبد خرید {self.user.phone if self.user else 'مهمان'}"

    @property
    def items_total(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def discount_amount(self):
        if self.coupon and self.coupon.is_valid:
            return self.coupon.calculate_discount(self.items_total)
        return 0

    @property
    def total(self):
        return self.items_total - self.discount_amount

    @property
    def items_count(self):
        return self.items.count()


class CartItem(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        return f"{self.cart} — {self.product.name} x{self.quantity}"

    @property
    def unit_price(self):
        if self.variant:
            return self.variant.price
        return self.product.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity


# ─────────────────────────────────────────
#  ORDER
# ─────────────────────────────────────────
class Order(models.Model):

    class Status(models.TextChoices):
        PENDING    = 'pending',    'در انتظار پرداخت'
        PROCESSING = 'processing', 'در حال پردازش'
        SHIPPED    = 'shipped',    'ارسال شده'
        DELIVERED  = 'delivered',  'تحویل داده شد'
        CANCELLED  = 'cancelled',  'لغو شده'
        RETURNED   = 'returned',   'مرجوع شده'

    class PaymentStatus(models.TextChoices):
        PENDING  = 'pending',  'در انتظار پرداخت'
        PAID     = 'paid',     'پرداخت شده'
        FAILED   = 'failed',   'ناموفق'
        REFUNDED = 'refunded', 'بازگشت داده شده'

    class PaymentMethod(models.TextChoices):
        ONLINE      = 'online',      'پرداخت آنلاین'
        WALLET      = 'wallet',      'کیف پول'
        CARD_TO_CARD = 'card2card',  'کارت به کارت'
        COD         = 'cod',         'پرداخت در محل'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_number    = models.CharField(max_length=20, unique=True, verbose_name='شماره سفارش')

    # ── Snapshot آدرس در لحظه خرید ──
    # نباید FK به Address باشد — آدرس ممکن است حذف شود
    address_snapshot = models.JSONField(verbose_name='آدرس تحویل')

    shipping_method  = models.ForeignKey(ShippingMethod, on_delete=models.PROTECT, null=True)
    shipping_cost    = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    coupon           = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount  = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    items_total      = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='جمع اقلام')
    total_amount     = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ کل')

    payment_method   = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.ONLINE)
    payment_status   = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    status           = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

    tracking_code    = models.CharField(max_length=50, blank=True, verbose_name='کد رهگیری')
    carrier          = models.CharField(max_length=50, blank=True, verbose_name='شرکت حمل')
    note             = models.TextField(blank=True, verbose_name='یادداشت مشتری')

    paid_at          = models.DateTimeField(null=True, blank=True)
    shipped_at       = models.DateTimeField(null=True, blank=True)
    delivered_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"#{self.order_number} — {self.user.phone}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        """ساخت شماره سفارش یکتا: SAB-1404-XXXXX"""
        year = timezone.now().year - 621  # تبدیل تقریبی به شمسی
        random_part = ''.join(random.choices(string.digits, k=5))
        return f"SAB-{year}-{random_part}"

    def set_status(self, status, description='', changed_by=None):
        """تغییر وضعیت با ثبت تاریخچه"""
        self.status = status
        if status == Order.Status.SHIPPED:
            self.shipped_at = timezone.now()
        elif status == Order.Status.DELIVERED:
            self.delivered_at = timezone.now()
        self.save()
        OrderStatusHistory.objects.create(
            order=self,
            status=status,
            description=description,
            changed_by=changed_by,
        )


# ─────────────────────────────────────────
#  ORDER ITEM — Snapshot محصول در لحظه خرید
# ─────────────────────────────────────────
class OrderItem(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # FK به محصول — ولی اگر محصول حذف شد، سفارش هنوز معتبر است
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant      = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)

    # ── Snapshot اطلاعات محصول در لحظه خرید ──
    # این فیلدها حتی اگر محصول حذف/تغییر کند، درست می‌مانند
    product_name = models.CharField(max_length=255, verbose_name='نام محصول')
    product_sku  = models.CharField(max_length=100, verbose_name='کد محصول')
    variant_name = models.CharField(max_length=100, blank=True, verbose_name='وریانت')
    unit_price   = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت واحد')
    quantity     = models.PositiveIntegerField(verbose_name='تعداد')

    class Meta:
        db_table = 'order_items'
        verbose_name = 'قلم سفارش'
        verbose_name_plural = 'اقلام سفارش'

    def __str__(self):
        return f"{self.order.order_number} — {self.product_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity


# ─────────────────────────────────────────
#  ORDER STATUS HISTORY — تایم‌لاین سفارش
# ─────────────────────────────────────────
class OrderStatusHistory(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status      = models.CharField(max_length=15, choices=Order.Status.choices)
    description = models.TextField(blank=True, verbose_name='توضیح')
    changed_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='تغییر داده شده توسط')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_histories'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.order.order_number} → {self.get_status_display()}"
