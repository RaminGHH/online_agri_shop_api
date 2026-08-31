import uuid
from django.db import models
from django.contrib.auth import get_user_model

class BaseModel(models.Model):
    """
    مدل پایه برای همه جداول سیستم.
    همه مدل‌ها باید از این ارث‌بری کنند.
 
    مزایا:
      - UUID به عنوان PK (نه integer قابل حدس)
      - created_at و updated_at خودکار
      - حذف واقعی ممنوع → همه مدل‌ها Soft Delete دارند
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')

    class Meta:
        abstract = True
        ordering = ['-created_at']



class SoftDeleteQuerySet(models.Model):
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)    

    def delete(self):
        """Soft delete — هرگز از دیتابیس حذف نمی‌شود"""
        return self.update(is_deleted=True)
    
    def hard_delete(self):
        """فقط ادمین و فقط در موارد خاص"""
        return super().delete()
    


class SoftDeleteManager(models.Model):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()
    
    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()    
    

class SoftDeleteModel(BaseModel):
    """
    مدل پایه برای مدل‌هایی که نباید حذف شوند.
    مثال: Product, Category, Order
 
    استفاده:
      obj.delete()       → is_deleted=True (Soft)
      obj.hard_delete()  → حذف واقعی (فقط ادمین)
      obj.restore()      → بازگشت از حذف
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_deleted"
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, deleted_by=None, *args, **kwargs):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=['is_deleted','deleted_at', 'deleted_by'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

class AuditLog(models.Model):
    """
    ثبت تمام تغییرات حساس سیستم.
    append-only — هرگز ویرایش یا حذف نمی‌شود.
 
    چه چیزهایی ثبت می‌شود:
      - تغییر نقش / وضعیت کاربر
      - تغییر Permission
      - تغییر وضعیت سفارش
      - تنظیمات مالی
      - عملیات ادمین
    """
    class Action(models.TextChoices):
        CREATE   = "create",   "ایجاد"
        UPDATE   = "update",   "ویرایش"
        DELETE   = "delete",   "حذف"
        RESTORE  = "restore",  "بازگشت"
        LOGIN    = "login",    "ورود"
        LOGOUT   = "logout",   "خروج"
        BLOCK    = "block",    "مسدود کردن"
        UNBLOCK  = "unblock",  "رفع مسدودیت"
        REFUND   = "refund",   "بازگشت وجه"
        EXPORT   = "export",   "خروجی"
        GRANT    = "grant",    "اعطای دسترسی"
        REVOKE   = "revoke",   "لغو دسترسی"
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # === Who ===
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs',
        verbose_name='انجام دهنده'
    )

    actor_phone = models.CharField(
        max_length=11,
        blank=True
    )

    # === What to do ===
    action = models.CharField(
        max_length=20,
        choices=Action.choices
    )

    # === On what ===
    resource_type = models.CharField(max_length=50) # "User" / "Order" / "Product"
    resource_id = models.CharField(max_length=36)

    # === Changes ===
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True)

    # === Request information ===
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=36, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        db_table = 'audit_logs'
        verbose_name = 'گزارش تغییر'
        verbose_name_plural = 'گزارش‌های تغییر'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'created_at']),

        ]
    
    def __str__(self):
        return f'{self.actor_phone} - {self.action} - {self.resource_type}:{self.resource_id}'
    
    @classmethod
    def log(cls, actor, action, resource, old=None, new=None, description='', request=None):
        """
        helper for easier logging:

        AuditLog.log(
            actor=request.user,
            action=AuditLog.Action.UPDATE,
            resource=order,
            old={"status": "pending"},
            new={"status": "processing"},
            request=request,
        )
        """
        cls.objects.create(
            actor=actor,
            actor_phone=actor.phone if actor else '',
            action=action,
            resource_type=type(resource).__name__,
            resource_id=str(resource.pk),
            old_value=old,
            new_value=new,
            description=description,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            request_id=request.META.get("HTTP_X_REQUEST_ID", "") if request else "",
        )