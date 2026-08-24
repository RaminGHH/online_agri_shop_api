"""
=============================================
  سبزینه — models.py
  Apps: payments, reviews, blog, notifications
=============================================
"""

import uuid
from django.db import models
from apps.accounts.models import User
from apps.products.models import Product
from apps.orders.models import Order


# ═══════════════════════════════════════════
#  APP: payments
# ═══════════════════════════════════════════

class Transaction(models.Model):

    class Gateway(models.TextChoices):
        ZARINPAL = 'zarinpal', 'زرین‌پال'
        MELLAT   = 'mellat',   'بانک ملت'
        WALLET   = 'wallet',   'کیف پول'

    class Status(models.TextChoices):
        PENDING  = 'pending',  'در انتظار'
        SUCCESS  = 'success',  'موفق'
        FAILED   = 'failed',   'ناموفق'
        REFUNDED = 'refunded', 'بازگشت داده شده'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user             = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions')
    order            = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)

    gateway          = models.CharField(max_length=20, choices=Gateway.choices)
    amount           = models.DecimalField(max_digits=12, decimal_places=0)
    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # اطلاعات درگاه
    authority        = models.CharField(max_length=100, blank=True)   # زرین‌پال
    transaction_id   = models.CharField(max_length=100, blank=True)   # شناسه تراکنش
    ref_id           = models.CharField(max_length=100, blank=True)   # شماره مرجع بانک
    gateway_response = models.JSONField(default=dict, blank=True)     # پاسخ کامل درگاه

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['authority']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.phone} — {self.amount} — {self.get_status_display()}"


# ═══════════════════════════════════════════
#  APP: reviews
# ═══════════════════════════════════════════

class Review(models.Model):

    RATING_CHOICES = [(i, i) for i in range(1, 6)]

    id                   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product              = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user                 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')

    rating               = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name='امتیاز')
    title                = models.CharField(max_length=200, blank=True, verbose_name='عنوان')
    body                 = models.TextField(verbose_name='متن نظر')
    admin_reply          = models.TextField(blank=True, verbose_name='پاسخ ادمین')

    is_approved          = models.BooleanField(default=False, verbose_name='تأیید شده')
    is_verified_purchase = models.BooleanField(default=False, verbose_name='خرید تأیید شده')
    likes_count          = models.PositiveIntegerField(default=0)

    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']
        # هر کاربر فقط یک نظر برای هر محصول
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.phone} — {self.product.name} ({self.rating}★)"


class ReviewLike(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review     = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_likes'
        unique_together = ['review', 'user']


# ═══════════════════════════════════════════
#  APP: blog
# ═══════════════════════════════════════════

class BlogCategory(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100, verbose_name='نام')
    slug        = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'blog_categories'
        ordering = ['order']

    def __str__(self):
        return self.name


class Tag(models.Model):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, verbose_name='برچسب')
    slug = models.SlugField(unique=True, allow_unicode=True)

    class Meta:
        db_table = 'blog_tags'

    def __str__(self):
        return self.name


class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT     = 'draft',     'پیش‌نویس'
        PUBLISHED = 'published', 'منتشر شده'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category         = models.ForeignKey(BlogCategory, on_delete=models.PROTECT, related_name='posts')
    author           = models.ForeignKey(User, on_delete=models.PROTECT, related_name='posts')
    tags             = models.ManyToManyField(Tag, blank=True, db_table='post_tags')

    title            = models.CharField(max_length=300, verbose_name='عنوان')
    slug             = models.SlugField(max_length=350, unique=True, allow_unicode=True)
    cover_image      = models.ImageField(upload_to='blog/', null=True, blank=True)
    excerpt          = models.CharField(max_length=500, blank=True, verbose_name='خلاصه')
    body             = models.TextField(verbose_name='محتوا')

    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    views_count      = models.PositiveIntegerField(default=0)
    read_time        = models.PositiveSmallIntegerField(default=5, verbose_name='زمان مطالعه (دقیقه)')

    meta_title       = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    published_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


# ═══════════════════════════════════════════
#  APP: notifications
# ═══════════════════════════════════════════

class Notification(models.Model):

    class Type(models.TextChoices):
        ORDER_PLACED   = 'order_placed',   'ثبت سفارش'
        ORDER_SHIPPED  = 'order_shipped',  'ارسال سفارش'
        ORDER_DELIVERED = 'order_delivered', 'تحویل سفارش'
        PAYMENT_SUCCESS = 'payment_success', 'پرداخت موفق'
        LOW_STOCK      = 'low_stock',      'موجودی کم'
        NEW_REVIEW     = 'new_review',     'نظر جدید'
        SYSTEM         = 'system',         'سیستمی'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=Type.choices)
    title      = models.CharField(max_length=200, verbose_name='عنوان')
    body       = models.TextField(verbose_name='متن')
    data       = models.JSONField(default=dict, blank=True)  # لینک، شناسه سفارش، ...
    is_read    = models.BooleanField(default=False, verbose_name='خوانده شده')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} — {self.title}"


class NotificationSetting(models.Model):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    order_updates_sms = models.BooleanField(default=True)
    marketing_sms     = models.BooleanField(default=True)
    email_newsletter  = models.BooleanField(default=False)

    class Meta:
        db_table = 'notification_settings'

    def __str__(self):
        return f"تنظیمات اعلان {self.user.phone}"
