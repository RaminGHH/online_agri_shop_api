"""
===============================================
Docstring for apps.accounts.models
Base on: API Contract v1.0 + SRS SESSION 4
===============================================


TABLES:
    - users
    - user_sessions
    - otp_codes
    - user_addresses
    - wallet_transactions
"""

import re
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator
from django.db.models import Q

# ======================
# USER MANAGER
# ======================
class UserManager(BaseUserManager):
    """
    Custom Manager of User model. 
    
    Responsible for creating regular users and superusers
    and normalizing mobile numbers before storing. 
    
    Since the system authentication is done based on mobile number, 
    phone is used as the primary user identifier.
    """
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required!")
        phone = self.normalize_phone(phone)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', self.model.Status.ACTIVE)
        extra_fields.setdefault('is_phone_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)
    
    @staticmethod
    def normalize_phone(phone):
        phone = str(phone).strip().replace(' ', '').replace('-', '')

        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('98'):
            phone = '0' + phone[2:]

        if not re.fullmatch(r'09\d{9}', phone):
            raise ValueError('Invalid Iranian mobile number.')

        return phone
    


# ======================
# USER 
# ======================
class User(AbstractBaseUser, PermissionsMixin):
    """
    The main identity of all system users.
    Login only with mobile number + OTP.
    """
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'مشتری'
        PERSONNEL = 'personnel', 'پرسنل داخلی'
        SELLER = 'seller', 'فروشنده'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'فعال'
        SUSPENDED = 'suspended', 'تعلیق'
        BLOCKED = 'blocked', 'مسدود'

    # === Identification === 
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )    

    # === Authentication ===
    phone = models.CharField(
        max_length=11, unique=True,
        verbose_name='شماره موبایل'
    )

    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name='موبایل تایید شده'
    )

    # === Profile ===
    first_name = models.CharField(
        max_length=50, blank=True,
        verbose_name='نام'
    )

    last_name = models.CharField(
        max_length=50, blank=True,
        verbose_name='نام خانوادگی'
    )

    email = models.EmailField(
        blank=True,
        verbose_name='ایمیل'
    )

    national_code_validator = RegexValidator(
        regex=r'^0\d{9}$',
        message='کد ملی باید با 0 شروع شده و 10 رقم باشد.'
    )
    national_code = models.CharField(
        max_length=10, 
        unique=True,
        blank=True,
        validators=[national_code_validator],
        verbose_name='کد ملی'
    )

    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')

    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True, blank=True, verbose_name='تصویر پروفایل'
    )

    # === Role ===
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='نقش'
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='وضعیت حساب'
    )

    status_reason = models.TextField(
        blank=True,
        verbose_name='دلیل تغییر وضعیت'
    )

    # === Wallet ===
    # This field is for quick display only
    # The actual value is calculated from the WalletTransaction (append-only ledger)
    wallet_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='موجودی کیف پول'
    )

    # === news ====
    sms_marketing = models.BooleanField(default=True, verbose_name='پیامک تبلیغاتی')
    email_marketing = models.BooleanField(default=True, verbose_name='ایمیل مارکتینگ')

    # === admin ===
    admin_note = models.TextField(blank=True, verbose_name='یادداشت مدیر')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # === permissions of admin pannel ===
    is_staff = models.BooleanField(default=False)

    # === timing ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت نام'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS =  []

    class Meta:
        db_table = 'users'
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})"
    
    def get_full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.phone

    # === shortcuts ===
    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE
    
    def can_login(self):
        """
        Is this user allowed to log in?
        """
        return (
            self.is_active
            and self.is_phone_verified
        )
    
    def suspend(self, reason=''):
        self.status = self.Status.SUSPENDED
        self.status_reason = reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])

    def block(self, reason=''):
        self.status = self.Status.BLOCKED
        self.status_reason = reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])
    
    def activate(self, reason=''):
        self.status = self.Status.ACTIVE
        self.status_reason = reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])



# ======================
# OTP CODE
# ======================
class OTPCode(models.Model):
    """
    One-time password used for authentication operations.

    OTP codes are never stored in plain text.

    Rules:
        - Each OTP is valid for a limited time.
        - Each OTP can only be used once.
        - Failed verification attempts are limited.
        - Only one active OTP should exist for each phone/purpose pair.

    Supported purposes:
        - LOGIN: User login.
        - REGISTER: User registration.
        - CHANGE_PHONE: Change user's phone number.
        - FORGOT_PASSWORD: Password recovery.
    """

    class Purpose(models.TextChoices):
        LOGIN = "login", "ورود"
        REGISTER = "register", "ثبت نام"
        CHANGE_PHONE = "change_phone", "تغییر شماره"
        FORGOT_PASSWORD = "forgot_password", "فراموشی رمز"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    phone = models.CharField(
        max_length=11,
        verbose_name="شماره موبایل",
    )

    code_hash = models.CharField(
        max_length=128,
        verbose_name="هش کد",
    )

    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        verbose_name="هدف",
    )

    # === Limits ===

    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )

    max_attempts = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="حداکثر تلاش",
    )

    # === Status ===

    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
    )

    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد",
    )

    class Meta:
        db_table = "otp_codes"

        verbose_name = "کد OTP"
        verbose_name_plural = "کدهای OTP"

        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["phone", "purpose", "is_used"]
            ),
            models.Index(
                fields=["phone", "purpose", "created_at"]
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["phone", "purpose"],
                condition=Q(is_used=False),
                name="unique_active_otp_per_phone_purpose",
            ),
        ]

    def __str__(self):
        status = "used" if self.is_used else "active"

        return (
            f"{self.phone} - "
            f"{self.get_purpose_display()} - "
            f"{status}"
        )

    @staticmethod
    def make_hash(code: str) -> str:
        """
        Securely hash an OTP before storing it.
        """
        return make_password(code)

    def check_code(self, code: str) -> bool:
        """
        Compare a plain OTP with its stored hash.
        """
        return check_password(
            str(code),
            self.code_hash,
        )

    @property
    def is_expired(self) -> bool:
        """
        Whether the OTP has expired.
        """
        return timezone.now() >= self.expires_at

    @property
    def is_max_attempts_reached(self) -> bool:
        """
        Whether the verification attempt limit has been reached.
        """
        return self.attempts >= self.max_attempts

    @property
    def is_valid(self) -> bool:
        """
        Whether the OTP can currently be used.
        """
        return (
            not self.is_used
            and not self.is_expired
            and not self.is_max_attempts_reached
        )

    def consume(self):
        """
        Permanently mark the OTP as used.
        """
        self.is_used = True

        self.save(
            update_fields=["is_used"]
        )
        


# ======================
# USER SESSION
# ======================
class UserSession(models.Model):
    """
    Active sessions per user.
    Each Refresh Token is a Session.
    Managed from the endpoint /api/v1/me/sessions/.
    """