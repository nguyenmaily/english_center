"""
Management command để tự động chuyển các enrollment pending → overdue khi quá hạn
Chạy định kỳ (cron job hoặc celery task) để kiểm tra và cập nhật
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from enrollment.models import Enrollment
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cập nhật trạng thái enrollment từ pending sang overdue khi quá hạn thanh toán'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị các enrollment sẽ được cập nhật, không thực sự cập nhật',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.now().date()
        
        # Tìm các enrollment pending và đã quá hạn
        overdue_enrollments = Enrollment.objects.filter(
            invoice_status='pending',
            due_date__lt=today
        ).exclude(due_date__isnull=True)
        
        count = overdue_enrollments.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Không có enrollment nào cần cập nhật.')
            )
            return
        
        self.stdout.write(f'Tìm thấy {count} enrollment cần cập nhật:')
        
        updated_count = 0
        for enrollment in overdue_enrollments:
            self.stdout.write(
                f'  - Enrollment {enrollment.id}: '
                f'Student {enrollment.student_id}, '
                f'Class {enrollment.class_field_id}, '
                f'Due date: {enrollment.due_date}, '
                f'Amount: {enrollment.amount}'
            )
            
            if not dry_run:
                enrollment.invoice_status = 'overdue'
                enrollment.save(update_fields=['invoice_status', 'updated_at'])
                updated_count += 1
                logger.info(f'Updated enrollment {enrollment.id} to overdue')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: Sẽ cập nhật {count} enrollment. '
                    'Chạy lại không có --dry-run để thực sự cập nhật.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nĐã cập nhật {updated_count} enrollment từ pending sang overdue.'
                )
            )


