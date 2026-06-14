from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class UserManager(BaseUserManager):
    """
    Custom manager responsible for creating and managing users.

    Provides helper methods for creating standard users and
    superusers while ensuring required authentication fields
    are validated and passwords are securely hashed.
    """
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")

        user = self.model(
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            phone_number,
            password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Represents a platform user.

    The User model is the central identity object of the system
    and acts as the owner of customer-related resources such as
    profiles, addresses, shopping carts, orders, reviews, and
    wishlist items.

    Security Features:
        - Password hashing via AbstractBaseUser
        - Permission management via PermissionsMixin
        - Custom authentication support
        - JWT compatibility

    Identification:
        - Primary: phone_number
        - Secondary: email

    Notes:
        This model is designed to support future authentication
        mechanisms such as OTP, SMS verification, and social login.
    """
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True
    )

    phone_number = models.CharField(
        max_length=11,
        unique=True
    )

    full_name = models.CharField(
        max_length=255,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_staff = models.BooleanField(
        default=False
    )

    date_joined = models.DateTimeField(
        auto_now_add=True
    )

    objects = UserManager()

    USERNAME_FIELD = "phone_number"

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number
    

class Profile(models.Model):
    """
    Stores additional user information that is not directly
    related to authentication.

    This model extends the User model and contains profile
    data used for personalization and account management.

    Related Model:
        - User
    """
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="profile"
    )

    avatar = models.ImageField(
        upload_to="avatars",
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True
    )

    birth_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.phone_number} Profile"
    

class Address(models.Model):
    """
    Represents a user's shipping or billing address.

    Multiple addresses can belong to a single user.
    One address can be marked as the default address.

    Related Model:
        - User
        - Order
    """
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    full_name = models.CharField(
        max_length=255
    )

    phone_number = models.CharField(
        max_length=11
    )

    province = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100
    )

    postal_code = models.CharField(
        max_length=20
    )

    street_address = models.TextField()

    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.full_name} - {self.city}"