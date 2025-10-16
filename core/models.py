from django.db import models
import uuid

class BaseModel(models.Model):
    """
    Abstract base model cung cấp khóa chính UUID (id), created_at, và updated_at.
    Mô hình này tuân thủ cấu trúc của schema database bạn cung cấp.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Abstract là bắt buộc để mô hình này không được tạo thành bảng riêng
        # mà chỉ dùng để thừa kế cho các mô hình khác.
        abstract = True
        ordering = ['-created_at']

