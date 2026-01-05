"""
Signals để tự động cập nhật StudentCertificate khi có kết quả final test
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from tests.models import ExamResult, ExamInstance
from .models import StudentCertificate
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ExamResult)
def update_proficiency_from_final_test(sender, instance, created, **kwargs):
    """
    Tự động cập nhật StudentCertificate khi có kết quả final test hoặc placement test
    
    Chỉ xử lý khi:
    - ExamResult có status = 'completed'
    - ExamInstance có exam_type = 'final' hoặc 'placement'
    - Score đã được tính (không null)
    
    QUAN TRỌNG - Tránh xung đột với chức năng upload chứng chỉ:
    - Chỉ động vào records có source_type='entry_test' hoặc 'final_test'
    - KHÔNG động vào records có source_type='certificate' (chứng chỉ upload)
    - Filter theo source_type để đảm bảo không xung đột
    """
    # Chỉ xử lý khi exam đã completed và có score
    if instance.status != 'completed' or instance.score is None:
        return
    
    try:
        # Lấy exam instance để kiểm tra exam_type
        exam_instance = ExamInstance.objects.get(id=instance.exam_instance_id)
        
        # Chỉ xử lý final test hoặc placement test (KHÔNG lưu midterm test)
        if exam_instance.exam_type not in ['final', 'placement']:
            return
        
        # Lấy student
        from users.models import Student
        try:
            student = Student.objects.get(id=instance.student_id)
        except Student.DoesNotExist:
            logger.warning(f"Student not found: {instance.student_id}")
            return
        
        # Xác định skill_group từ exam
        # Có thể dựa vào title hoặc questions trong exam
        # Tạm thời, cần xác định từ exam_instance hoặc questions
        # Giả sử có thể xác định từ exam_instance.title hoặc questions
        skill_group = _determine_skill_group_from_exam(exam_instance)
        
        if not skill_group:
            logger.warning(f"Could not determine skill_group for exam {exam_instance.id}")
            return
        
        # Tính điểm theo skill_group
        # Score từ ExamResult là % (0-100), cần convert sang điểm TOEIC
        total_score = _convert_percentage_to_toeic_score(float(instance.score), skill_group)
        
        if total_score is None:
            logger.warning(f"Could not convert score {instance.score} to TOEIC score")
            return
        
        # Xác định source_type
        # QUAN TRỌNG: Chỉ động vào entry_test và final_test, KHÔNG động vào certificate và midterm_test
        # Để tránh xung đột với chức năng upload chứng chỉ (source_type='certificate')
        # KHÔNG lưu midterm_test vào student_certificates
        if exam_instance.exam_type == 'placement':
            source_type = StudentCertificate.SourceType.ENTRY_TEST
        else:  # final
            source_type = StudentCertificate.SourceType.FINAL_TEST
        
        # Tìm record mới nhất với cùng source_type và skill_group
        # CHỈ tìm records có source_type='entry_test' hoặc 'final_test'
        # KHÔNG động vào records có source_type='certificate' (chứng chỉ upload) hoặc 'midterm_test'
        latest_certificate = StudentCertificate.objects.filter(
            student=student,
            source_type=source_type,  # Filter theo entry_test, midterm_test hoặc final_test
            skill_group=skill_group
        ).order_by('-test_date', '-created_at').first()
        
        test_date = timezone.now().date()
        test_type_name = 'placement test' if exam_instance.exam_type == 'placement' else 'final test'
        
        if latest_certificate:
            # Luôn update record mới nhất với kết quả test mới nhất
            # Đảm bảo kết quả test gần nhất luôn được lưu vào bảng student_certificates
            old_score = latest_certificate.total_score
            old_test_date = latest_certificate.test_date
            
            latest_certificate.total_score = total_score
            latest_certificate.test_date = test_date
            latest_certificate.expired_date = StudentCertificate.calculate_expired_date_for_test()
            latest_certificate.status = StudentCertificate.Status.VERIFIED
            latest_certificate.verification_method = StudentCertificate.VerificationMethod.AUTO_OCR
            latest_certificate.save()
            
            certificate = latest_certificate
            created = False
            logger.info(f"✅ Updated latest {test_type_name} certificate (ID: {latest_certificate.id}) for student {student.id}, skill_group {skill_group}, score: {old_score} → {total_score}, test_date: {old_test_date} → {test_date}")
        else:
            # Tạo mới nếu chưa có record nào
            certificate = StudentCertificate.objects.create(
                student=student,
                source_type=source_type,
                skill_group=skill_group,
                total_score=total_score,
                test_date=test_date,
                expired_date=StudentCertificate.calculate_expired_date_for_test(),
                status=StudentCertificate.Status.VERIFIED,
                verification_method=StudentCertificate.VerificationMethod.AUTO_OCR,
            )
            created = True
            logger.info(f"✅ Created new {test_type_name} certificate (ID: {certificate.id}) for student {student.id}, skill_group {skill_group}, score {total_score}")
    
    except ExamInstance.DoesNotExist:
        logger.warning(f"ExamInstance not found: {instance.exam_instance_id}")
    except Exception as e:
        logger.error(f"Error updating proficiency from final test: {e}", exc_info=True)


def _determine_skill_group_from_exam(exam_instance):
    """
    Xác định skill_group từ exam instance
    
    Có thể dựa vào:
    - exam_instance.title (nếu có chứa "LR", "SW", "Listening-Reading", etc.)
    - Questions trong exam (kiểm tra skill của questions)
    """
    title = exam_instance.title.upper() if exam_instance.title else ""
    
    # Kiểm tra title
    if 'LR' in title or 'LISTENING' in title and 'READING' in title:
        return StudentCertificate.SkillGroup.LR
    elif 'SW' in title or 'SPEAKING' in title and 'WRITING' in title:
        return StudentCertificate.SkillGroup.SW
    
    # Nếu không xác định được từ title, kiểm tra questions
    try:
        from tests.models import ExamInstanceQuestion, Question
        exam_questions = ExamInstanceQuestion.objects.filter(exam_instance_id=exam_instance.id)
        
        if exam_questions.exists():
            # Lấy skill từ question đầu tiên
            first_question = Question.objects.filter(
                id=exam_questions.first().question_id
            ).first()
            
            if first_question and first_question.skill:
                skill = first_question.skill.upper()
                if 'LISTENING' in skill or 'READING' in skill:
                    return StudentCertificate.SkillGroup.LR
                elif 'SPEAKING' in skill or 'WRITING' in skill:
                    return StudentCertificate.SkillGroup.SW
    except Exception as e:
        logger.warning(f"Error determining skill_group from questions: {e}")
    
    return None


def _convert_percentage_to_toeic_score(percentage, skill_group):
    """
    Convert điểm % (0-100) sang điểm TOEIC
    
    Args:
        percentage: float (0-100)
        skill_group: StudentCertificate.SkillGroup.LR hoặc StudentCertificate.SkillGroup.SW
    
    Returns:
        int: Điểm TOEIC (LR: 0-990, SW: 0-400)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Converting percentage: {percentage}, skill_group: {skill_group}, type: {type(skill_group)}")
    
    # So sánh với cả enum value và string để đảm bảo hoạt động đúng
    if skill_group == StudentCertificate.SkillGroup.LR or str(skill_group) == 'LR':
        # Convert % sang điểm LR (0-990)
        # Giả sử: 0% = 0, 100% = 990
        score = int(percentage * 9.9)
        logger.debug(f"Converted to LR score: {score}")
        return score
    elif skill_group == StudentCertificate.SkillGroup.SW or str(skill_group) == 'SW':
        # Convert % sang điểm SW (0-400)
        # Giả sử: 0% = 0, 100% = 400
        score = int(percentage * 4.0)
        logger.debug(f"Converted to SW score: {score}")
        return score
    
    logger.warning(f"Unknown skill_group: {skill_group}, defaulting to LR")
    # Mặc định là LR nếu không xác định được
    return int(percentage * 9.9)


