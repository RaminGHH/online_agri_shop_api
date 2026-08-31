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
    updated_At = models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')