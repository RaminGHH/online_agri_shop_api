"""
=============================================
  سبزینه — models.py
  App: accounts
  جداول: User, Address, OTPCode, WalletTransaction
=============================================
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ─────────────────────────────────────────
#  USER MANAGER
# ─────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('شماره موبایل الزامی است')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(phone, password, **extra_fields)


# ─────────────────────────────────────────
#  USER
# ─────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'مشتری'
        GOLD     = 'gold',     'کاربر طلایی'
        STAFF    = 'staff',    'کارمند'
        ADMIN    = 'admin',    'مدیر'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone           = models.CharField(max_length=11, unique=True, verbose_name='موبایل')
    email           = models.EmailField(blank=True, verbose_name='ایمیل')
    first_name      = models.CharField(max_length=50, blank=True, verbose_name='نام')
    last_name       = models.CharField(max_length=50, blank=True, verbose_name='نام خانوادگی')
    national_code   = models.CharField(max_length=10, blank=True, verbose_name='کد ملی')
    birth_date      = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    avatar          = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='تصویر پروفایل')

    role            = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER, verbose_name='نقش')
    is_verified     = models.BooleanField(default=False, verbose_name='تأیید شده')
    is_active       = models.BooleanField(default=True, verbose_name='فعال')
    is_staff        = models.BooleanField(default=False)

    # کیف پول
    wallet_balance  = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='موجودی کیف پول')

    # تنظیمات اطلاع‌رسانی
    sms_marketing   = models.BooleanField(default=True, verbose_name='پیامک تبلیغاتی')
    email_marketing = models.BooleanField(default=False, verbose_name='ایمیل خبرنامه')

    # یادداشت ادمین
    admin_note      = models.TextField(blank=True, verbose_name='یادداشت ادمین')

    created_at      = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عضویت')
    updated_at      = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        db_table    = 'users'
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering    = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})"

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.phone

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_gold(self):
        return self.role == self.Role.GOLD


# ─────────────────────────────────────────
#  OTP CODE
# ─────────────────────────────────────────
class OTPCode(models.Model):

    class Purpose(models.TextChoices):
        REGISTER         = 'register',         'ثبت‌نام'
        LOGIN            = 'login',            'ورود'
        FORGOT_PASSWORD  = 'forgot_password',  'فراموشی رمز'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone      = models.CharField(max_length=11, verbose_name='موبایل')
    code       = models.CharField(max_length=6, verbose_name='کد')
    purpose    = models.CharField(max_length=20, choices=Purpose.choices, verbose_name='هدف')
    is_used    = models.BooleanField(default=False, verbose_name='استفاده شده')
    expires_at = models.DateTimeField(verbose_name='زمان انقضا')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_codes'
        verbose_name = 'کد OTP'
        verbose_name_plural = 'کدهای OTP'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone} — {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


# ─────────────────────────────────────────
#  ADDRESS
# ─────────────────────────────────────────
class Address(models.Model):

    PROVINCES = [
        ('tehran',      'تهران'),
        ('isfahan',     'اصفهان'),
        ('khorasan',    'خراسان رضوی'),
        ('alborz',      'البرز'),
        ('mazandaran',  'مازندران'),
        ('fars',        'فارس'),
        ('east_azarb',  'آذربایجان شرقی'),
        ('west_azarb',  'آذربایجان غربی'),
        ('khuzestan',   'خوزستان'),
        ('kermanshah',  'کرمانشاه'),
        ('other',       'سایر'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='کاربر')
    title           = models.CharField(max_length=50, verbose_name='عنوان آدرس')  # خانه، محل کار
    receiver_name   = models.CharField(max_length=100, verbose_name='نام گیرنده')
    receiver_phone  = models.CharField(max_length=11, verbose_name='موبایل گیرنده')
    province        = models.CharField(max_length=20, choices=PROVINCES, verbose_name='استان')
    city            = models.CharField(max_length=50, verbose_name='شهر')
    address         = models.TextField(verbose_name='آدرس کامل')
    postal_code     = models.CharField(max_length=10, verbose_name='کد پستی')
    is_default      = models.BooleanField(default=False, verbose_name='پیش‌فرض')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'user_addresses'
        verbose_name = 'آدرس'
        verbose_name_plural = 'آدرس‌ها'
        ordering    = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.title}"

    def save(self, *args, **kwargs):
        # اگر این آدرس به عنوان پیش‌فرض انتخاب شد،
        # آدرس‌های دیگر را از حالت پیش‌فرض خارج کن
        if self.is_default:
            Address.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────
#  WALLET TRANSACTION
# ─────────────────────────────────────────
class WalletTransaction(models.Model):

    class Type(models.TextChoices):
        CHARGE  = 'charge',  'شارژ'
        SPEND   = 'spend',   'خرج'
        REFUND  = 'refund',  'بازگشت وجه'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    type            = models.CharField(max_length=10, choices=Type.choices, verbose_name='نوع')
    amount          = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ')
    balance_after   = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='موجودی بعد از تراکنش')
    description     = models.CharField(max_length=255, blank=True, verbose_name='توضیح')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'wallet_transactions'
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering    = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} — {self.get_type_display()} — {self.amount}"
