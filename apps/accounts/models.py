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

import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


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
        extra_fields.setdefault('is_staff', True),
        extra_fields.setdefault('is_superuser', True),
        extra_fields.setdefault('status', 'active'),
        extra_fields.setdefault('is_phone_verified', True)
        return self.create_user(phone, password, **extra_fields)
    
    @staticmethod
    def normalize_phone():
        """
        Normalize phone for Iran
        """
        phone = str(phone).strip().replace(' ','').replace('-','')
        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('98') and len(phone) == 12:
            phone = '0' + phone[2:]
        return phone
    

# ======================
# USER 
# ======================
class User(AbstractBaseUser, PermissionsMixin):
    """
    The main identity of all system users.
    Login only with mobile number + OTP.

    PROPERTIES:
    id, 
    phone, is_phone_verified
    first_name, last_name, email, national_code, birth_date, avatar
    role, status, status_reason
    wallet_balance
    sms_marketing, email_marketing
    admin_note, last_login_ip, last_login_at
    is_staff, is_active
    created_at, updated_at

    get_full_name()
    is_admin()
    is_active()
    can_login()
    suspend()
    block()
    active()
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

    national_code = models.CharField(
        max_length=10, blank=True,
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
    last_login_at = models.DateField(null=True, blank=True)

    # === permissions of admin pannel ===
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # === timing ===
    created_at = models.DateField(auto_now_add=True, verbose_name='تاریخ ثبت نام')
    updated_at = models.DateField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS =  []

    class Meta:
        db_table = 'users'
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status', 'role']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})"
    
    def get_full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.phone

    # === shortcuts ===
    @property
    def is_admin(self):
        return self.role == self.role.ADMIN

    @property
    def is_active(self):
        return self.status == self.status.ACTIVE
    
    def can_login(self):
        """
        Is this user allowed to log in?
        """
        return self.is_active and self.status != self.status.BLOCKED
    
    def suspend(self, reason='', by=None):
        self.status = self.status.SUSPENDED
        self.status_reason =reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])

    def block(self, reason, by=None):
        self.status = self.status.BLOCKED
        self.status_reason = reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])
    
    def active(self, reason, by=None):
        self.status = self.status.ACTIVE
        self.status_reason = reason
        self.save(update_fields=['status', 'status_reason', 'updated_at'])



# ======================
# OTP CODE
# ======================
class OTPCode(models.Model):
    """
    One-time code for authentication.
    The code is stored as a hash (security).
    """