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
        extra_fields.setdefault('is_active', True),
        extra_fields.setdefault('role', 'admin'),
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
    




