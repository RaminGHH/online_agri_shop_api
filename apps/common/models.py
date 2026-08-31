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
        ordering = ['created_at']



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