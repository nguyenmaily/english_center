from django.db import models
from core.models import BaseModel
import uuid


class Campus(BaseModel):
    """
    Model representing a campus/cơ sở
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    address = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'campuses'
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


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
