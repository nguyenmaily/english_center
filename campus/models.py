from django.db import models
from core.models import BaseModel
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Campus(BaseModel):
    """
    Model representing a campus/cơ sở
    """
    STATUS_CHOICES = [
        ('active', 'Hoạt động'),
        ('inactive', 'Ngừng hoạt động'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    address = models.TextField(null=True, blank=True)
    hotline = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    # NOTE: Manager relationship is via ManagerProfile.campus (reverse relationship)
    # NOT via Campus.manager (forward relationship)
    # To get manager: ManagerProfile.objects.filter(campus=this_campus).first()
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    description = models.TextField(null=True, blank=True)
    facilities = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'campuses'
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def code(self):
        """
        Trả về 8 ký tự đầu của UUID làm code
        VD: a1b2c3d4-e5f6-... -> A1B2C3D4
        """
        return str(self.id).split('-')[0].upper()


class Room(BaseModel):
    """
    Model representing a room/phòng
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    is_under_repair = models.BooleanField(default=False)
    campus = models.ForeignKey(
        Campus,
        on_delete=models.RESTRICT,
        related_name='rooms'
    )
    
    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.campus.name}"


class Equipment(BaseModel):
    """
    Model representing equipment/thiết bị
    """
    class EquipmentStatus(models.TextChoices):
        WORKING = 'working', 'Working'
        BROKEN = 'broken', 'Broken'
        MAINTENANCE = 'maintenance', 'Maintenance'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    quantity = models.IntegerField(default=1, help_text="Số lượng thiết bị")
    status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.WORKING
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='equipments'
    )
    
    class Meta:
        db_table = 'equipment'
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.room.name}"