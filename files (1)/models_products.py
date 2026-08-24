"""
=============================================
  سبزینه — models.py
  App: products
  جداول: Category, Brand, Product, ProductImage,
         ProductAttribute, ProductVariant, Wishlist
=============================================
"""

import uuid
from django.db import models
from django.utils.text import slugify
from apps.accounts.models import User


# ─────────────────────────────────────────
#  CATEGORY — درختی نامحدود
# ─────────────────────────────────────────
class Category(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Self-referential — کلید طلایی قابل توسعه بودن
    # کشاورزی → کود → کود آلی → هیومیک اسید
    # دیجیتال → موبایل → آیفون → آیفون ۱۶
    parent      = models.ForeignKey(
                    'self',
                    null=True, blank=True,
                    related_name='children',
                    on_delete=models.SET_NULL,
                    verbose_name='دسته والد'
                  )

    name        = models.CharField(max_length=100, verbose_name='نام')
    slug        = models.SlugField(max_length=120, unique=True, allow_unicode=True, verbose_name='اسلاگ')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    image       = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name='تصویر')
    icon        = models.CharField(max_length=10, blank=True, verbose_name='آیکون emoji')

    is_active   = models.BooleanField(default=True, verbose_name='فعال')
    show_in_nav = models.BooleanField(default=False, verbose_name='نمایش در منو')
    order       = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')

    meta_title       = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'categories'
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering    = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} ← {self.name}"
        return self.name

    @property
    def is_root(self):
        return self.parent is None

    def get_ancestors(self):
        """برگرداندن تمام اجداد یک دسته (برای breadcrumb)"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_all_children_ids(self):
        """برگرداندن ID تمام زیردسته‌ها (برای فیلتر محصولات)"""
        ids = [self.id]
        for child in self.children.filter(is_active=True):
            ids.extend(child.get_all_children_ids())
        return ids


# ─────────────────────────────────────────
#  BRAND
# ─────────────────────────────────────────
class Brand(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100, verbose_name='نام برند')
    slug        = models.SlugField(max_length=120, unique=True, allow_unicode=True)
    logo        = models.ImageField(upload_to='brands/', null=True, blank=True, verbose_name='لوگو')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'brands'
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'
        ordering    = ['name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
#  PRODUCT
# ─────────────────────────────────────────
class Product(models.Model):

    class Unit(models.TextChoices):
        KG      = 'kg',      'کیلوگرم'
        GRAM    = 'g',       'گرم'
        LITER   = 'liter',   'لیتر'
        PIECE   = 'piece',   'عدد'
        PACKAGE = 'package', 'بسته'
        METER   = 'meter',   'متر'
        SET     = 'set',     'ست'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category         = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='دسته‌بندی')
    brand            = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='برند')

    # ── اطلاعات پایه ──
    name             = models.CharField(max_length=255, verbose_name='نام محصول')
    slug             = models.SlugField(max_length=280, unique=True, allow_unicode=True)
    description      = models.TextField(verbose_name='توضیحات کامل')
    short_description = models.CharField(max_length=500, blank=True, verbose_name='توضیح کوتاه')

    # ── قیمت‌گذاری ──
    price            = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت فروش')
    compare_price    = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='قیمت قبل از تخفیف')
    cost_price       = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='قیمت تمام‌شده')

    # ── موجودی ──
    stock            = models.IntegerField(default=0, verbose_name='موجودی')
    low_stock_threshold = models.IntegerField(default=5, verbose_name='حداقل موجودی هشدار')
    sku              = models.CharField(max_length=100, unique=True, verbose_name='کد محصول')
    weight           = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='وزن (گرم)')
    unit             = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE, verbose_name='واحد')

    # ── مشخصات اضافه (JSON) — برای نمایش ──
    # این فیلد برای هر حوزه متفاوت است:
    # کشاورزی: {"درصد_هیومیک": "70%", "روش_مصرف": "محلول‌پاشی"}
    # موبایل: {"RAM": "8GB", "حافظه": "256GB", "پردازنده": "A18"}
    specs_json       = models.JSONField(default=dict, blank=True, verbose_name='مشخصات (JSON)')

    # ── وضعیت ──
    is_active        = models.BooleanField(default=True, verbose_name='فعال')
    is_featured      = models.BooleanField(default=False, verbose_name='محصول ویژه')

    # ── آمار ──
    views_count      = models.PositiveIntegerField(default=0, verbose_name='بازدید')
    sales_count      = models.PositiveIntegerField(default=0, verbose_name='تعداد فروش')

    # ── سئو ──
    meta_title       = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'products'
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering    = ['-created_at']
        indexes     = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['-sales_count']),
        ]

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return round((1 - self.price / self.compare_price) * 100)
        return 0

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if not reviews.exists():
            return 0
        return round(reviews.aggregate(
            avg=models.Avg('rating')
        )['avg'], 1)


# ─────────────────────────────────────────
#  PRODUCT IMAGE
# ─────────────────────────────────────────
class ProductImage(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image    = models.ImageField(upload_to='products/', verbose_name='تصویر')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='متن جایگزین')
    is_main  = models.BooleanField(default=False, verbose_name='تصویر اصلی')
    order    = models.PositiveIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        db_table = 'product_images'
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} — تصویر {self.order}"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────
#  PRODUCT ATTRIBUTE — EAV داینامیک
# ─────────────────────────────────────────
class ProductAttribute(models.Model):
    """
    مشخصات فنی قابل فیلتر کردن
    کشاورزی: key="درصد هیومیک"  value="70%"
    موبایل:  key="RAM"           value="8GB"
    یخچال:   key="حجم"           value="450 لیتر"
    """
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    key     = models.CharField(max_length=100, verbose_name='ویژگی')
    value   = models.CharField(max_length=500, verbose_name='مقدار')
    order   = models.PositiveIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        db_table = 'product_attributes'
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} | {self.key}: {self.value}"


# ─────────────────────────────────────────
#  PRODUCT VARIANT — سایز، رنگ، ظرفیت
# ─────────────────────────────────────────
class ProductVariant(models.Model):
    """
    کود هیومیک:  بسته 1kg / بسته 5kg / بسته 25kg
    موبایل:      آبی 128GB / مشکی 256GB / تیتانیوم 512GB
    لباس:        سایز S / M / L / XL
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product      = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name         = models.CharField(max_length=100, verbose_name='نام وریانت')
    sku          = models.CharField(max_length=100, unique=True, verbose_name='کد')
    price        = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت')
    compare_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    stock        = models.IntegerField(default=0, verbose_name='موجودی')
    weight       = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    order        = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_variants'
        ordering = ['order', 'price']

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    @property
    def is_in_stock(self):
        return self.stock > 0


# ─────────────────────────────────────────
#  WISHLIST
# ─────────────────────────────────────────
class Wishlist(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'wishlists'
        unique_together = ['user', 'product']
        ordering   = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} ← {self.product.name}"
