import random
from datetime import datetime
from rest_framework import viewsets, serializers, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max
from django.db import models
import logging
import unicodedata
from .models import (
    Question, QuestionGroup, ExamBlueprint, ExamRule, 
    ExamInstance, ExamInstanceQuestion, ExamResult, ExamAnswer, StudentProgress
)

logger = logging.getLogger(__name__)


def update_student_certificate_from_exam_result(exam_result):
    """
    Cập nhật StudentCertificate từ ExamResult
    
    Được gọi thủ công từ finish_exam vì ExamResult có managed=False
    nên signal post_save không tự động trigger khi update bằng raw SQL.
    
    Logic:
    - Tìm record mới nhất với cùng source_type và skill_group
    - Nếu có và test_date khác nhau → Tạo mới (lưu lịch sử)
    - Nếu có và test_date giống nhau → Update record đó
    - Nếu không có → Tạo mới
    
    Đảm bảo kết quả test gần nhất luôn được lưu vào bảng student_certificates.
    """
    try:
        logger.info(f"🔄 ===== STARTING certificate update =====")
        print(f"[UPDATE_CERTIFICATE] 🔄 ===== STARTING certificate update =====")
        logger.info(f"🔄 Exam result ID: {exam_result.id}")
        print(f"[UPDATE_CERTIFICATE] 🔄 Exam result ID: {exam_result.id}")
        logger.info(f"🔄 Status: {exam_result.status}")
        print(f"[UPDATE_CERTIFICATE] 🔄 Status: {exam_result.status}")
        logger.info(f"🔄 Score: {exam_result.score} (type: {type(exam_result.score)})")
        print(f"[UPDATE_CERTIFICATE] 🔄 Score: {exam_result.score} (type: {type(exam_result.score)})")
        logger.info(f"🔄 Student ID: {exam_result.student_id}")
        print(f"[UPDATE_CERTIFICATE] 🔄 Student ID: {exam_result.student_id}")
        logger.info(f"🔄 Exam Instance ID: {exam_result.exam_instance_id}")
        print(f"[UPDATE_CERTIFICATE] 🔄 Exam Instance ID: {exam_result.exam_instance_id}")
        logger.info(f"🔄 Submitted At: {exam_result.submitted_at}")
        print(f"[UPDATE_CERTIFICATE] 🔄 Submitted At: {exam_result.submitted_at}")
        
        # Chỉ xử lý khi exam đã completed và có score
        if exam_result.status != 'completed' or exam_result.score is None:
            logger.warning(f"⚠️ Skipping certificate update: status={exam_result.status}, score={exam_result.score}")
            print(f"[UPDATE_CERTIFICATE] ⚠️ Skipping certificate update: status={exam_result.status}, score={exam_result.score}")
            return
        
        # Lấy exam instance để kiểm tra exam_type
        exam_instance = ExamInstance.objects.get(id=exam_result.exam_instance_id)
        logger.info(f"📋 Exam instance: {exam_instance.id}, title={exam_instance.title}, exam_type={exam_instance.exam_type}")
        print(f"[UPDATE_CERTIFICATE] 📋 Exam instance: {exam_instance.id}, title={exam_instance.title}, exam_type={exam_instance.exam_type}")
        
        # Nếu exam_instance không có exam_type, lấy từ blueprint
        exam_type = exam_instance.exam_type
        if not exam_type and exam_instance.blueprint_id:
            try:
                blueprint = ExamBlueprint.objects.get(id=exam_instance.blueprint_id)
                exam_type = blueprint.exam_type
                logger.info(f"📋 Using exam_type from blueprint: {exam_type}")
                print(f"[UPDATE_CERTIFICATE] 📋 Using exam_type from blueprint: {exam_type}")
            except ExamBlueprint.DoesNotExist:
                logger.warning(f"⚠️ Blueprint not found: {exam_instance.blueprint_id}")
                print(f"[UPDATE_CERTIFICATE] ⚠️ Blueprint not found: {exam_instance.blueprint_id}")
        
        # Chỉ xử lý final test, midterm test hoặc placement test
        if exam_type not in ['final', 'midterm', 'placement']:
            logger.warning(f"⚠️ Skipping certificate update: exam_type={exam_type} (not 'final', 'midterm' or 'placement')")
            print(f"[UPDATE_CERTIFICATE] ⚠️ Skipping certificate update: exam_type={exam_type} (not 'final', 'midterm' or 'placement')")
            return
        
        # Cập nhật exam_instance.exam_type để sử dụng trong các bước tiếp theo
        exam_instance.exam_type = exam_type
        
        # Import StudentCertificate trước khi sử dụng
        from proficiency.models import StudentCertificate
        
        # Lấy student
        from users.models import Student
        try:
            student = Student.objects.get(id=exam_result.student_id)
            logger.info(f"✅ Student found: {student.id}")
            print(f"[UPDATE_CERTIFICATE] ✅ Student found: {student.id}")
        except Student.DoesNotExist:
            logger.warning(f"⚠️ Student not found: {exam_result.student_id}")
            print(f"[UPDATE_CERTIFICATE] ⚠️ Student not found: {exam_result.student_id}")
            return
        
        # Xác định skill_group từ exam
        skill_group = _determine_skill_group_from_exam_for_certificate(exam_instance)
        
        # Mặc định skill_group là LR nếu không xác định được
        # Đảm bảo luôn có skill_group để lưu vào student_certificates
        if not skill_group:
            logger.info(f"⚠️ Could not determine skill_group for exam {exam_instance.id}, using default LR")
            skill_group = StudentCertificate.SkillGroup.LR
        else:
            logger.info(f"✅ Determined skill_group: {skill_group} for exam {exam_instance.id}")
        
        # Tính điểm theo skill_group
        # Score từ ExamResult là % (0-100), cần convert sang điểm TOEIC
        from proficiency.signals import _convert_percentage_to_toeic_score
        
        logger.info(f"🔄 Converting score: {exam_result.score}% (type: {type(exam_result.score)}), skill_group: {skill_group} (type: {type(skill_group)})")
        
        try:
            total_score = _convert_percentage_to_toeic_score(float(exam_result.score), skill_group)
            logger.info(f"📊 Score conversion result: {exam_result.score}% → {total_score} TOEIC ({skill_group})")
        except Exception as conv_error:
            logger.error(f"❌ Error converting score: {str(conv_error)}", exc_info=True)
            return
        
        if total_score is None:
            logger.error(f"❌ Could not convert score {exam_result.score}% to TOEIC score for skill_group {skill_group}")
            return
        
        logger.info(f"✅ Successfully converted score: {exam_result.score}% → {total_score} TOEIC")
        
        # Xác định source_type (sử dụng exam_type đã được xác định ở trên)
        if exam_type == 'placement':
            source_type = StudentCertificate.SourceType.ENTRY_TEST
        elif exam_type == 'midterm':
            source_type = StudentCertificate.SourceType.MIDTERM_TEST
        else:  # final
            source_type = StudentCertificate.SourceType.FINAL_TEST
        
        # Lấy test_date từ exam_result.submitted_at
        from django.utils import timezone
        test_date = exam_result.submitted_at.date() if exam_result.submitted_at else timezone.now().date()
        
        # Tìm record mới nhất với cùng source_type và skill_group
        # CHỈ tìm records có source_type='entry_test', 'midterm_test' hoặc 'final_test'
        # KHÔNG động vào records có source_type='certificate' (chứng chỉ upload)
        latest_certificate = StudentCertificate.objects.filter(
            student=student,
            source_type=source_type,  # Filter theo entry_test, midterm_test hoặc final_test
            skill_group=skill_group
        ).order_by('-test_date', '-created_at').first()
        
        test_type_name = 'placement test' if exam_type == 'placement' else ('midterm test' if exam_type == 'midterm' else 'final test')
        
        logger.info(f"🔍 Looking for existing certificate: student={student.id}, source_type={source_type}, skill_group={skill_group}")
        logger.info(f"📊 Certificate data to save: total_score={total_score}, test_date={test_date}, source_type={source_type}, skill_group={skill_group}")
        
        if latest_certificate:
            # Luôn update record mới nhất với kết quả test mới nhất
            # Đảm bảo kết quả test gần nhất luôn được lưu vào bảng student_certificates
            old_score = latest_certificate.total_score
            old_test_date = latest_certificate.test_date
            
            logger.info(f"📝 Updating existing certificate ID: {latest_certificate.id}, old_score: {old_score}, new_score: {total_score}")
            
            latest_certificate.total_score = total_score
            latest_certificate.test_date = test_date
            latest_certificate.expired_date = StudentCertificate.calculate_expired_date_for_test()
            latest_certificate.status = StudentCertificate.Status.VERIFIED
            latest_certificate.verification_method = StudentCertificate.VerificationMethod.AUTO_OCR
            
            try:
                latest_certificate.save()
                logger.info(f"✅ Successfully updated latest {test_type_name} certificate (ID: {latest_certificate.id}) for student {student.id}, skill_group {skill_group}, score: {old_score} → {total_score}, test_date: {old_test_date} → {test_date}")
            except Exception as save_error:
                logger.error(f"❌ Error saving certificate: {str(save_error)}", exc_info=True)
                raise
        else:
            # Tạo mới nếu chưa có record nào
            logger.info(f"📝 Creating new certificate for student {student.id}")
            try:
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
                logger.info(f"✅ Successfully created new {test_type_name} certificate (ID: {certificate.id}) for student {student.id}, skill_group {skill_group}, score {total_score}, test_date {test_date}")
            except Exception as create_error:
                logger.error(f"❌ Error creating certificate: {str(create_error)}", exc_info=True)
                raise
    
    except ExamInstance.DoesNotExist:
        logger.warning(f"ExamInstance not found: {exam_result.exam_instance_id}")
    except Exception as e:
        logger.error(f"Error updating StudentCertificate from exam result: {e}", exc_info=True)
        raise


def _determine_skill_group_from_exam_for_certificate(exam_instance):
    """
    Xác định skill_group từ exam instance
    
    Helper function để xác định skill_group từ exam title hoặc questions
    Nếu không xác định được, trả về None (sẽ được xử lý ở hàm gọi)
    """
    from proficiency.models import StudentCertificate
    
    title = exam_instance.title.upper() if exam_instance.title else ""
    
    # Kiểm tra title
    if 'LR' in title or ('LISTENING' in title and 'READING' in title):
        return StudentCertificate.SkillGroup.LR
    elif 'SW' in title or ('SPEAKING' in title and 'WRITING' in title):
        return StudentCertificate.SkillGroup.SW
    
    # Nếu không xác định được từ title, kiểm tra questions
    try:
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
            
            # Nếu không có skill trong question, kiểm tra part
            if first_question and first_question.part:
                part = first_question.part.upper()
                # Part 1-4 thường là Listening, Part 5-7 thường là Reading
                if 'PART' in part:
                    part_num = part.replace('PART', '').strip()
                    try:
                        part_num_int = int(part_num)
                        if part_num_int <= 4:
                            return StudentCertificate.SkillGroup.LR
                        elif part_num_int >= 5:
                            return StudentCertificate.SkillGroup.LR  # Reading cũng là LR
                    except ValueError:
                        pass
    except Exception as e:
        logger.warning(f"Error determining skill_group from questions: {e}")
    
    # Nếu không xác định được, trả về None (sẽ được xử lý ở hàm gọi)
    return None


class QuestionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionGroup
        fields = '__all__'
    
    def to_representation(self, instance):
        """Handle encoding issues"""
        try:
            data = super().to_representation(instance)
            # Handle encoding issues in text fields
            text_fields = ['part', 'skill', 'context']
            for field in text_fields:
                if data.get(field):
                    data[field] = self._clean_text(data[field])
            return data
        except Exception as e:
            logger.error(f"Serialization error for question group {instance.id}: {str(e)}")
            return {
                'id': str(instance.id),
                'part': self._clean_text(instance.part) if instance.part else None,
                'skill': self._clean_text(instance.skill) if instance.skill else None,
                'context': self._clean_text(instance.context) if instance.context else None,
                'audio_file': instance.audio_file,
                'image_file': instance.image_file,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
            }
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            # Normalize unicode
            text = unicodedata.normalize('NFKD', str(text))
            # Replace Vietnamese characters
            replacements = {
                'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        except Exception as e:
            logger.warning(f"Text cleaning error: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
    
    def to_representation(self, instance):
        """Handle encoding issues"""
        try:
            data = super().to_representation(instance)
            # Handle encoding issues in text fields
            text_fields = ['part', 'skill', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            for field in text_fields:
                if data.get(field):
                    data[field] = self._clean_text(data[field])
            return data
        except Exception as e:
            logger.error(f"Serialization error for question {instance.id}: {str(e)}")
            return {
                'id': str(instance.id),
                'group_id': str(instance.group_id) if instance.group_id else None,
                'part': self._clean_text(instance.part) if hasattr(instance, 'part') and instance.part else None,
                'skill': self._clean_text(instance.skill) if hasattr(instance, 'skill') and instance.skill else None,
                'text': self._clean_text(instance.text) if instance.text else None,
                'option_a': self._clean_text(instance.option_a) if instance.option_a else None,
                'option_b': self._clean_text(instance.option_b) if instance.option_b else None,
                'option_c': self._clean_text(instance.option_c) if instance.option_c else None,
                'option_d': self._clean_text(instance.option_d) if instance.option_d else None,
                'correct_answer': self._clean_text(instance.correct_answer) if instance.correct_answer else None,
                'audio_file': getattr(instance, 'audio_file', None),
                'difficulty': instance.difficulty,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
            }
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            # Normalize unicode
            text = unicodedata.normalize('NFKD', str(text))
            # Replace Vietnamese characters
            replacements = {
                'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        except Exception as e:
            logger.warning(f"Text cleaning error: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')


class ExamRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRule
        fields = '__all__'


class ExamBlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamBlueprint
        fields = '__all__'


class ExamInstanceSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    exam_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamInstance
        fields = '__all__'
    
    def get_class_name(self, obj):
        """Get class name if class_id exists"""
        if obj.class_id:
            try:
                from classes.models import Class
                class_obj = Class.objects.get(id=obj.class_id)
                return class_obj.name if class_obj.name else None
            except Class.DoesNotExist:
                return None
        return None
    
    def get_exam_type_display(self, obj):
        """Get exam type - from blueprint if exists, otherwise from exam_instance"""
        if obj.blueprint_id:
            try:
                blueprint = ExamBlueprint.objects.get(id=obj.blueprint_id)
                return blueprint.exam_type if blueprint.exam_type else None
            except ExamBlueprint.DoesNotExist:
                pass
        # For manual exams, use exam_type from ExamInstance
        return obj.exam_type if obj.exam_type else None


class ExamResultSerializer(serializers.ModelSerializer):
    exam_instance_title = serializers.SerializerMethodField()
    exam_type = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamResult
        fields = '__all__'
    
    def get_exam_instance_title(self, obj):
        """Get exam instance title"""
        try:
            exam = ExamInstance.objects.get(id=obj.exam_instance_id)
            return self._clean_text(exam.title) if exam.title else None
        except ExamInstance.DoesNotExist:
            return None
    
    def get_exam_type(self, obj):
        """Get exam type from blueprint"""
        try:
            exam = ExamInstance.objects.get(id=obj.exam_instance_id)
            if exam.blueprint_id:
                blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                return blueprint.exam_type if blueprint.exam_type else None
        except (ExamInstance.DoesNotExist, ExamBlueprint.DoesNotExist):
            pass
        return None
    
    def get_class_name(self, obj):
        """Get class name from exam instance"""
        try:
            exam = ExamInstance.objects.get(id=obj.exam_instance_id)
            if exam.class_id:
                from classes.models import Class
                class_obj = Class.objects.get(id=exam.class_id)
                return self._clean_text(class_obj.name) if class_obj.name else None
        except (ExamInstance.DoesNotExist, Class.DoesNotExist):
            pass
        return None
    
    def get_student_name(self, obj):
        """Get student name"""
        try:
            from users.models import Student
            student = Student.objects.get(id=obj.student_id)
            if student.user_account:
                return student.user_account.fullname if student.user_account.fullname else None
        except Student.DoesNotExist:
            pass
        return None
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')
        except:
            return str(text)


class StudentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgress
        fields = '__all__'


# Question Group Views
class QuestionGroupViewSet(viewsets.ModelViewSet):
    queryset = QuestionGroup.objects.all().order_by('-created_at')
    serializer_class = QuestionGroupSerializer

    def list(self, request, *args, **kwargs):
        """Override list method to add error handling"""
        try:
            logger.info("Fetching question groups list")
            # Use Django ORM with individual field handling
            queryset = QuestionGroup.objects.all().order_by('-created_at')
            results = []
            
            for obj in queryset:
                try:
                    # Create a clean representation with safe field access
                    result = {
                        'id': str(obj.id),
                        'audio_file': obj.audio_file,
                        'image_file': obj.image_file,
                        'created_at': obj.created_at,
                        'updated_at': obj.updated_at,
                    }
                    
                    # Try to access text fields safely
                    try:
                        result['part'] = self._clean_text(obj.part) if obj.part else None
                    except Exception as e:
                        logger.warning(f"Error accessing part field for {obj.id}: {str(e)}")
                        result['part'] = 'Error loading data'
                    
                    try:
                        result['skill'] = self._clean_text(obj.skill) if obj.skill else None
                    except Exception as e:
                        logger.warning(f"Error accessing skill field for {obj.id}: {str(e)}")
                        result['skill'] = 'Error loading data'
                    
                    try:
                        result['context'] = self._clean_text(obj.context) if obj.context else None
                    except Exception as e:
                        logger.warning(f"Error accessing context field for {obj.id}: {str(e)}")
                        result['context'] = 'Error loading data'
                    
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing question group {obj.id}: {str(e)}")
                    # Add minimal data for problematic records
                    results.append({
                        'id': str(obj.id),
                        'part': 'Error loading data',
                        'skill': 'Error loading data',
                        'context': 'Error loading data',
                        'audio_file': None,
                        'image_file': None,
                        'created_at': None,
                        'updated_at': None,
                    })
            
            logger.info(f"Successfully fetched {len(results)} question groups")
            return Response(results)
                
        except Exception as e:
            logger.error(f"Error fetching question groups: {str(e)}")
            # Return empty list instead of error
            return Response([])

    def create(self, request, *args, **kwargs):
        """Override create method to handle encoding and file uploads"""
        try:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            from datetime import datetime
            
            # Handle file uploads
            data = request.data.copy()
            
            # Handle image file upload (only from file, not URL)
            if 'image_file' in request.FILES:
                image_file = request.FILES['image_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"question_groups/image_{timestamp}_{image_file.name}"
                file_path = default_storage.save(filename, ContentFile(image_file.read()))
                data['image_file'] = default_storage.url(file_path)
            # If no file uploaded and creating new, set to None
            elif not id:
                data['image_file'] = None
            
            # Handle audio file upload (only from file, not URL)
            if 'audio_file' in request.FILES:
                audio_file = request.FILES['audio_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"question_groups/audio_{timestamp}_{audio_file.name}"
                file_path = default_storage.save(filename, ContentFile(audio_file.read()))
                data['audio_file'] = default_storage.url(file_path)
            # If no file uploaded and creating new, set to None
            elif not id:
                data['audio_file'] = None
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            # Clean text fields before saving
            validated_data = serializer.validated_data.copy()
            text_fields = ['part', 'skill', 'context']
            for field in text_fields:
                if field in validated_data and validated_data[field]:
                    validated_data[field] = self._clean_text(validated_data[field])
            
            instance = QuestionGroup.objects.create(**validated_data)
            response_serializer = self.get_serializer(instance)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"Error creating question group: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error creating question group: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """Override update method to handle encoding and file uploads"""
        try:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            from datetime import datetime
            
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Handle file uploads
            data = request.data.copy()
            
            # Handle image file upload (only from file, not URL)
            if 'image_file' in request.FILES:
                image_file = request.FILES['image_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"question_groups/image_{timestamp}_{image_file.name}"
                file_path = default_storage.save(filename, ContentFile(image_file.read()))
                data['image_file'] = default_storage.url(file_path)
            # Check if image should be deleted (empty string from FormData)
            elif 'image_file' in data and data['image_file'] == '':
                data['image_file'] = None
            # If partial update and no file provided, keep existing value
            elif partial:
                # Don't change existing value if not provided
                pass
            # If full update and no file provided, set to None (will clear existing)
            elif 'image_file' not in data:
                data['image_file'] = None
            
            # Handle audio file upload (only from file, not URL)
            if 'audio_file' in request.FILES:
                audio_file = request.FILES['audio_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"question_groups/audio_{timestamp}_{audio_file.name}"
                file_path = default_storage.save(filename, ContentFile(audio_file.read()))
                data['audio_file'] = default_storage.url(file_path)
            # Check if audio should be deleted (empty string from FormData)
            elif 'audio_file' in data and data['audio_file'] == '':
                data['audio_file'] = None
            # If partial update and no file provided, keep existing value
            elif partial:
                # Don't change existing value if not provided
                pass
            # If full update and no file provided, set to None (will clear existing)
            elif 'audio_file' not in data:
                data['audio_file'] = None
            
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Clean text fields before saving
            validated_data = serializer.validated_data.copy()
            text_fields = ['part', 'skill', 'context']
            for field in text_fields:
                if field in validated_data and validated_data[field]:
                    validated_data[field] = self._clean_text(validated_data[field])
            
            # Update instance
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            response_serializer = self.get_serializer(instance)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating question group: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error updating question group: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            # Normalize unicode
            text = unicodedata.normalize('NFKD', str(text))
            # Replace Vietnamese characters
            replacements = {
                'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        except Exception as e:
            logger.warning(f"Text cleaning error: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')


# Question Views
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('-created_at')
    serializer_class = QuestionSerializer

    def list(self, request, *args, **kwargs):
        """Override list method to add error handling"""
        try:
            logger.info("Fetching questions list")
            # Use raw SQL to handle encoding issues
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, group_id, part, skill, text, option_a, option_b, option_c, 
                           option_d, correct_answer, audio_file, difficulty, created_at, updated_at 
                    FROM questions 
                    ORDER BY created_at DESC
                """)
                columns = [col[0] for col in cursor.description]
                results = []
                for row in cursor.fetchall():
                    try:
                        row_dict = dict(zip(columns, row))
                        # Clean text fields
                        for field in ['part', 'skill', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']:
                            if row_dict.get(field):
                                row_dict[field] = self._clean_text(row_dict[field])
                        results.append(row_dict)
                    except Exception as e:
                        logger.warning(f"Error processing row: {str(e)}")
                        # Add minimal data for problematic records
                        results.append({
                            'id': str(row[0]) if row[0] else None,
                            'group_id': str(row[1]) if row[1] else None,
                            'part': str(row[2]) if len(row) > 2 and row[2] else None,
                            'skill': str(row[3]) if len(row) > 3 and row[3] else None,
                            'text': 'Error loading data',
                            'option_a': None,
                            'option_b': None,
                            'option_c': None,
                            'option_d': None,
                            'correct_answer': None,
                            'audio_file': str(row[10]) if len(row) > 10 and row[10] else None,
                            'difficulty': row[11] if len(row) > 11 else None,
                            'created_at': row[12] if len(row) > 12 else None,
                            'updated_at': row[13] if len(row) > 13 else None,
                        })
                
                logger.info(f"Successfully fetched {len(results)} questions")
                return Response(results)
                
        except Exception as e:
            logger.error(f"Error fetching questions: {str(e)}")
            # Fallback to empty list if database has issues
            return Response([])
    
    def create(self, request, *args, **kwargs):
        """Override create method to handle part, skill and file uploads"""
        try:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from datetime import datetime
            
            # Handle file uploads - process files first before copying data
            # Cannot use request.data.copy() when there are file uploads
            audio_file_url = None
            
            # Handle audio file upload
            if 'audio_file' in request.FILES:
                audio_file = request.FILES['audio_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"questions/audio_{timestamp}_{audio_file.name}"
                file_path = default_storage.save(filename, ContentFile(audio_file.read()))
                audio_file_url = default_storage.url(file_path)
            
            # Create data dict from request.data, excluding file fields
            data = {}
            for key, value in request.data.items():
                if key != 'audio_file':  # Skip audio_file as it's handled separately
                    data[key] = value
            
            # Add audio_file URL if uploaded
            data['audio_file'] = audio_file_url
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            # Clean text fields before saving
            validated_data = serializer.validated_data.copy()
            text_fields = ['part', 'skill', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            for field in text_fields:
                if field in validated_data and validated_data[field]:
                    validated_data[field] = self._clean_text(validated_data[field])
            
            instance = Question.objects.create(**validated_data)
            response_serializer = self.get_serializer(instance)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"Error creating question: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error creating question: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """Override update method to handle part, skill and file uploads"""
        try:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from datetime import datetime
            
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Handle file uploads
            data = request.data.copy()
            
            # Handle audio file upload
            if 'audio_file' in request.FILES:
                audio_file = request.FILES['audio_file']
                # Save file to media folder
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"questions/audio_{timestamp}_{audio_file.name}"
                file_path = default_storage.save(filename, ContentFile(audio_file.read()))
                data['audio_file'] = default_storage.url(file_path)
            elif 'audio_file' in data and data['audio_file'] is None:
                # Explicitly set to None to delete audio
                data['audio_file'] = None
            elif partial:
                # Partial update, don't change if not provided
                pass
            elif 'audio_file' not in data:
                data['audio_file'] = None
            
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # Clean text fields before saving
            validated_data = serializer.validated_data.copy()
            text_fields = ['part', 'skill', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            for field in text_fields:
                if field in validated_data and validated_data[field]:
                    validated_data[field] = self._clean_text(validated_data[field])
            
            # Update instance
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            response_serializer = self.get_serializer(instance)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Error updating question: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'detail': f'Error updating question: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            # Normalize unicode
            text = unicodedata.normalize('NFKD', str(text))
            # Replace Vietnamese characters
            replacements = {
                'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        except Exception as e:
            logger.warning(f"Text cleaning error: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')


# Exam Blueprint Views
class ExamBlueprintViewSet(viewsets.ModelViewSet):
    queryset = ExamBlueprint.objects.all().order_by('-created_at')
    serializer_class = ExamBlueprintSerializer
    search_fields = ['title', 'exam_type']
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    
    def get_queryset(self):
        """Override to add exam_type filtering"""
        queryset = super().get_queryset()
        exam_type = self.request.query_params.get('exam_type', None)
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
        return queryset

    @action(detail=True, methods=['post'], url_path='rules')
    def add_rule(self, request, pk=None):
        """Add rule to blueprint"""
        blueprint = self.get_object()
        rule_data = request.data.copy()
        rule_data['blueprint_id'] = blueprint.id
        serializer = ExamRuleSerializer(data=rule_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='rules')
    def list_rules(self, request, pk=None):
        """List rules for blueprint"""
        blueprint = self.get_object()
        rules = ExamRule.objects.filter(blueprint_id=blueprint.id)
        return Response(ExamRuleSerializer(rules, many=True).data)


# Exam Rule Views
class ExamRuleViewSet(viewsets.ModelViewSet):
    queryset = ExamRule.objects.all().order_by('-created_at')
    serializer_class = ExamRuleSerializer


# Exam Instance Views
class ExamInstanceViewSet(viewsets.ModelViewSet):
    queryset = ExamInstance.objects.all().order_by('-generated_at')
    serializer_class = ExamInstanceSerializer

    def list(self, request, *args, **kwargs):
        """Override list method to add error handling and pagination"""
        try:
            logger.info("Fetching exam instances list")
            
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Try using raw SQL first since model has managed=False
            from django.db import connection
            all_results = []
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT ei.id, ei.blueprint_id, ei.title, ei.status, ei.class_id, ei.exam_type, ei.generated_at, ei.created_by,
                               eb.title as blueprint_title,
                               eb.exam_type as blueprint_exam_type,
                               c.name as class_name
                        FROM exam_instances ei
                        LEFT JOIN exam_blueprints eb ON ei.blueprint_id = eb.id
                        LEFT JOIN classes c ON ei.class_id = c.id
                        ORDER BY ei.generated_at DESC
                    """)
                    columns = [col[0] for col in cursor.description]
                    
                    for row in cursor.fetchall():
                        row_dict = dict(zip(columns, row))
                        try:
                            result = {
                                'id': str(row_dict['id']),
                                'blueprint_id': str(row_dict['blueprint_id']) if row_dict['blueprint_id'] else None,
                                'blueprint_title': self._clean_text(row_dict['blueprint_title']) if row_dict['blueprint_title'] else None,
                                'class_id': str(row_dict['class_id']) if row_dict['class_id'] else None,
                                'class_name': self._clean_text(row_dict['class_name']) if row_dict['class_name'] else None,
                                'exam_type': row_dict.get('exam_type') if row_dict.get('exam_type') else None,
                                'exam_type_display': None,  # Will be set by serializer
                                'status': row_dict['status'] if row_dict['status'] else 'draft',
                                'generated_at': row_dict['generated_at'],
                                'created_by': str(row_dict['created_by']) if row_dict['created_by'] else None,
                            }
                            
                            # Clean title text
                            if row_dict['title']:
                                result['title'] = self._clean_text(row_dict['title'])
                            else:
                                result['title'] = None
                            
                            # Set exam_type_display: from blueprint if exists, otherwise from exam_instance
                            blueprint_exam_type = row_dict.get('blueprint_exam_type')
                            if result['blueprint_id'] and blueprint_exam_type:
                                # For exams with blueprint, exam_type_display comes from blueprint
                                result['exam_type_display'] = blueprint_exam_type
                            else:
                                # For manual exams, use exam_type from exam_instance
                                result['exam_type_display'] = result['exam_type']
                            
                            all_results.append(result)
                        except Exception as e:
                            logger.warning(f"Error processing exam instance row: {str(e)}")
                            continue
                
                logger.info(f"Successfully fetched {len(all_results)} exam instances using raw SQL")
                
            except Exception as sql_error:
                logger.warning(f"Raw SQL failed, trying ORM: {str(sql_error)}")
                # Fallback to ORM
                queryset = ExamInstance.objects.all().order_by('-generated_at')
                
                for obj in queryset:
                    try:
                        result = {
                            'id': str(obj.id),
                            'blueprint_id': str(obj.blueprint_id) if obj.blueprint_id else None,
                            'blueprint_title': None,
                            'class_id': str(obj.class_id) if obj.class_id else None,
                            'class_name': None,
                            'exam_type': obj.exam_type if obj.exam_type else None,
                            'exam_type_display': None,
                            'status': obj.status,
                            'generated_at': obj.generated_at,
                            'created_by': str(obj.created_by) if obj.created_by else None,
                        }
                        
                        # Get blueprint title and exam_type if blueprint_id exists
                        if obj.blueprint_id:
                            try:
                                blueprint = ExamBlueprint.objects.get(id=obj.blueprint_id)
                                result['blueprint_title'] = self._clean_text(blueprint.title) if blueprint.title else None
                                # For exams with blueprint, exam_type_display comes from blueprint
                                result['exam_type_display'] = blueprint.exam_type if blueprint.exam_type else None
                            except ExamBlueprint.DoesNotExist:
                                result['blueprint_title'] = None
                        else:
                            # For manual exams, exam_type_display comes from exam_instance
                            result['exam_type_display'] = obj.exam_type if obj.exam_type else None
                        
                        # Get class name if class_id exists
                        if obj.class_id:
                            try:
                                from classes.models import Class
                                class_obj = Class.objects.get(id=obj.class_id)
                                result['class_name'] = self._clean_text(class_obj.name) if class_obj.name else None
                            except Class.DoesNotExist:
                                result['class_name'] = None
                        
                        # Try to access text fields safely
                        try:
                            result['title'] = self._clean_text(obj.title) if obj.title else None
                        except Exception as e:
                            logger.warning(f"Error accessing title field for {obj.id}: {str(e)}")
                            result['title'] = 'Error loading data'
                        
                        all_results.append(result)
                    except Exception as e:
                        logger.warning(f"Error processing exam instance {obj.id}: {str(e)}")
                        continue
                
                logger.info(f"Successfully fetched {len(all_results)} exam instances using ORM")
            
            # Apply pagination manually
            total_count = len(all_results)
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_results = all_results[start_index:end_index]
            
            logger.info(f"Total exam instances: {total_count}, Page: {page}/{total_pages}, Returning: {len(paginated_results)}")
            
            # Return paginated response in CustomJSONRenderer format
            return Response({
                'count': total_count,
                'next': f"?page={page + 1}" if page < total_pages else None,
                'previous': f"?page={page - 1}" if page > 1 else None,
                'page_size': page_size,
                'total_pages': total_pages,
                'results': paginated_results
            })
                
        except Exception as e:
            logger.error(f"Error fetching exam instances: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty paginated response instead of error
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'page_size': 20,
                'total_pages': 1,
                'results': []
            })
    
    def _clean_text(self, text):
        """Clean text to avoid encoding issues"""
        if not text:
            return text
        try:
            # Normalize unicode
            text = unicodedata.normalize('NFKD', str(text))
            # Replace Vietnamese characters
            replacements = {
                'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text
        except Exception as e:
            logger.warning(f"Text cleaning error: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_exam(self, request):
        """Generate exam from blueprint"""
        blueprint_id = request.data.get('blueprint_id')
        name = request.data.get('name', 'Generated Exam')
        class_id = request.data.get('class_id', None)  # Optional class assignment
        
        try:
            blueprint = ExamBlueprint.objects.get(id=blueprint_id)
        except ExamBlueprint.DoesNotExist:
            return Response({'detail': 'Blueprint not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rules for this blueprint
        rules = ExamRule.objects.filter(blueprint_id=blueprint_id)
        selected_questions = []
        
        for rule in rules:
            # Get questions matching the rule criteria
            rule_questions = Question.objects.filter(
                difficulty=rule.difficulty
            )
            # Randomly select the required count
            selected = random.sample(list(rule_questions), min(rule.num_questions, len(rule_questions)))
            selected_questions.extend(selected)
        
        # Create exam instance
        # Copy exam_type from blueprint to exam_instance
        exam = ExamInstance.objects.create(
            blueprint_id=blueprint_id,
            title=name,
            status='published',
            class_id=class_id,  # Assign to class if provided
            exam_type=blueprint.exam_type if blueprint.exam_type else None  # Copy exam_type from blueprint
        )
        
        # Create exam instance questions
        for i, question in enumerate(selected_questions):
            ExamInstanceQuestion.objects.create(
                exam_instance_id=exam.id,
                question_id=question.id,
                order_number=i + 1
            )
        
        return Response(ExamInstanceSerializer(exam).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='manual')
    def create_manual_exam(self, request):
        """Create exam manually"""
        title = request.data.get('title')
        exam_type = request.data.get('exam_type', None)  # placement, midterm, final
        exam_status = request.data.get('status', 'draft')  # Renamed to avoid conflict with status module
        class_id = request.data.get('class_id', None)
        
        if not title:
            return Response({'detail': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not exam_type:
            return Response({'detail': 'exam_type is required for manual exams'}, status=status.HTTP_400_BAD_REQUEST)
        
        exam = ExamInstance.objects.create(
            title=title,
            exam_type=exam_type,  # Store exam_type for manual exams
            status=exam_status,  # Use renamed variable
            class_id=class_id
        )
        
        return Response(ExamInstanceSerializer(exam).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='questions')
    def get_exam_questions(self, request, pk=None):
        """Get all questions for an exam instance"""
        exam = self.get_object()
        
        # Get exam instance questions ordered by order_number
        exam_questions = ExamInstanceQuestion.objects.filter(
            exam_instance_id=exam.id
        ).order_by('order_number')
        
        questions_data = []
        for eq in exam_questions:
            try:
                question = Question.objects.get(id=eq.question_id)
                question_group = None
                if question.group_id:
                    try:
                        question_group = QuestionGroup.objects.get(id=question.group_id)
                    except QuestionGroup.DoesNotExist:
                        pass
                
                question_data = {
                    'id': str(question.id),
                    'order_number': eq.order_number,
                    'part': question.part,
                    'skill': question.skill,
                    'text': self._clean_text(question.text) if question.text else None,
                    'option_a': self._clean_text(question.option_a) if question.option_a else None,
                    'option_b': self._clean_text(question.option_b) if question.option_b else None,
                    'option_c': self._clean_text(question.option_c) if question.option_c else None,
                    'option_d': self._clean_text(question.option_d) if question.option_d else None,
                    'correct_answer': question.correct_answer,
                    'difficulty': question.difficulty,
                    'audio_file': question.audio_file,
                    'group_id': str(question.group_id) if question.group_id else None,
                    'group': None
                }
                
                # Add group info if exists
                if question_group:
                    question_data['group'] = {
                        'id': str(question_group.id),
                        'part': question_group.part,
                        'skill': question_group.skill,
                        'context': self._clean_text(question_group.context) if question_group.context else None,
                        'audio_file': question_group.audio_file,
                        'image_file': question_group.image_file
                    }
                
                questions_data.append(question_data)
            except Question.DoesNotExist:
                logger.warning(f"Question {eq.question_id} not found for exam instance {exam.id}")
                continue
            except Exception as e:
                logger.error(f"Error loading question {eq.question_id}: {str(e)}")
                continue
        
        return Response({
            'exam': ExamInstanceSerializer(exam).data,
            'questions': questions_data
        })
    
    @action(detail=True, methods=['post'], url_path='add-question')
    def add_question(self, request, pk=None):
        """Add a question to exam instance"""
        exam = self.get_object()
        question_id = request.data.get('question_id')
        order_number = request.data.get('order_number', None)
        
        if not question_id:
            return Response({'detail': 'question_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if question already exists in exam
        existing = ExamInstanceQuestion.objects.filter(
            exam_instance_id=exam.id,
            question_id=question_id
        ).first()
        
        if existing:
            return Response({'detail': 'Question already exists in this exam'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If order_number not provided, get the next order number
        if order_number is None:
            max_order = ExamInstanceQuestion.objects.filter(
                exam_instance_id=exam.id
            ).aggregate(Max('order_number'))['order_number__max']
            order_number = (max_order or 0) + 1
        
        # Create exam instance question
        exam_question = ExamInstanceQuestion.objects.create(
            exam_instance_id=exam.id,
            question_id=question_id,
            order_number=order_number
        )
        
        return Response({
            'id': str(exam_question.id),
            'exam_instance_id': str(exam_question.exam_instance_id),
            'question_id': str(exam_question.question_id),
            'order_number': exam_question.order_number
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove-question')
    def remove_question(self, request, pk=None):
        """Remove a question from exam instance"""
        exam = self.get_object()
        question_id = request.data.get('question_id')
        
        if not question_id:
            return Response({'detail': 'question_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exam_question = ExamInstanceQuestion.objects.get(
                exam_instance_id=exam.id,
                question_id=question_id
            )
            exam_question.delete()
            return Response({'detail': 'Question removed from exam'}, status=status.HTTP_204_NO_CONTENT)
        except ExamInstanceQuestion.DoesNotExist:
            return Response({'detail': 'Question not found in this exam'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='regenerate-questions')
    def regenerate_questions(self, request, pk=None):
        """Regenerate questions for exam instance from blueprint"""
        exam = self.get_object()
        
        if not exam.blueprint_id:
            return Response({
                'detail': 'Exam instance không có blueprint. Không thể regenerate questions.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
        except ExamBlueprint.DoesNotExist:
            return Response({'detail': 'Blueprint not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get rules for this blueprint
        rules = ExamRule.objects.filter(blueprint_id=exam.blueprint_id)
        
        if not rules.exists():
            return Response({
                'detail': 'Blueprint không có rules. Vui lòng thêm rules vào blueprint trước.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        selected_questions = []
        
        for rule in rules:
            # Get questions matching the rule criteria
            rule_questions = Question.objects.filter(
                difficulty=rule.difficulty
            )
            
            if len(rule_questions) < rule.num_questions:
                logger.warning(f"Not enough questions for rule {rule.id}. Required: {rule.num_questions}, Available: {len(rule_questions)}")
            
            # Randomly select the required count
            if len(rule_questions) > 0:
                selected = random.sample(list(rule_questions), min(rule.num_questions, len(rule_questions)))
                selected_questions.extend(selected)
        
        if len(selected_questions) == 0:
            return Response({
                'detail': 'Không tìm thấy câu hỏi phù hợp với rules của blueprint.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete existing questions
        ExamInstanceQuestion.objects.filter(exam_instance_id=exam.id).delete()
        
        # Create new exam instance questions
        for i, question in enumerate(selected_questions):
            ExamInstanceQuestion.objects.create(
                exam_instance_id=exam.id,
                question_id=question.id,
                order_number=i + 1
            )
        
        logger.info(f"Regenerated {len(selected_questions)} questions for exam {exam.id}")
        
        return Response({
            'detail': f'Đã thêm {len(selected_questions)} câu hỏi vào exam instance.',
            'total_questions': len(selected_questions)
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='placement-tests')
    def placement_tests(self, request):
        """
        GET /api/tests/exam-instances/placement-tests/?student_id={student_id}
        
        Lấy danh sách placement tests (LR và SW)
        """
        student_id_param = request.query_params.get('student_id')
        if not student_id_param:
            return Response({
                'success': False,
                'error': 'student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🔍 Placement tests API called with student_id_param: {student_id_param}")
        
        # Convert user_account_id to student_id if needed
        actual_student_id = None
        
        # If authenticated, try to get student from user account
        if request.user and request.user.is_authenticated:
            try:
                from users.models import Student
                student = Student.objects.filter(user_account_id=request.user.id).first()
                if student:
                    actual_student_id = student.id
                    logger.info(f"✅ Found student from authenticated user: {actual_student_id}")
            except Exception as e:
                logger.warning(f"Could not get student from authenticated user: {e}")
        
        # If not found from auth, try to use provided student_id_param
        # Check if it's a valid student_id (exists in students table)
        if not actual_student_id and student_id_param:
            try:
                from users.models import Student
                # Check if student_id_param is a student_id
                student = Student.objects.filter(id=student_id_param).first()
                if not student:
                    # Try to find by user_account_id (might be User ID)
                    student = Student.objects.filter(user_account_id=student_id_param).first()
                    if student:
                        logger.info(f"✅ Found student by user_account_id: {student_id_param} → {student.id}")
                if student:
                    actual_student_id = student.id
                    logger.info(f"✅ Found student from provided ID: {actual_student_id}")
                else:
                    logger.warning(f"❌ No student found for ID: {student_id_param}")
            except Exception as e:
                logger.error(f"Error converting student_id: {str(e)}", exc_info=True)
        
        if not actual_student_id:
            logger.warning(f"⚠️ Could not determine actual student_id, using provided: {student_id_param}")
            actual_student_id = student_id_param
        
        student_id = actual_student_id
        logger.info(f"📌 Using student_id: {student_id}")
        
        # Lọc exam instances với exam_type = 'placement'
        # Nếu exam_instance không có exam_type, check từ blueprint
        published_exams = ExamInstance.objects.filter(
            status='published'  # Chỉ lấy exam đã publish
        ).order_by('title')
        
        # Filter exams có exam_type='placement' hoặc blueprint có exam_type='placement'
        placement_exams = []
        for exam in published_exams:
            # Check exam_type từ exam_instance hoặc blueprint
            exam_type = exam.exam_type
            if not exam_type and exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_type = blueprint.exam_type if blueprint.exam_type else None
                except ExamBlueprint.DoesNotExist:
                    pass
            
            # Chỉ thêm nếu exam_type = 'placement'
            if exam_type == 'placement':
                placement_exams.append(exam)
        
        # Phân biệt LR và SW dựa vào title
        # Giả sử title có chứa "Listening" hoặc "Reading" → LR
        # Title có chứa "Speaking" hoặc "Writing" → SW
        result = []
        for exam in placement_exams:
            title_upper = exam.title.upper()
            skill_group = None
            
            if 'LISTENING' in title_upper or 'READING' in title_upper:
                skill_group = 'LR'
            elif 'SPEAKING' in title_upper or 'WRITING' in title_upper:
                skill_group = 'SW'
            
            # Lấy số câu hỏi từ exam instance questions
            question_count = ExamInstanceQuestion.objects.filter(
                exam_instance_id=exam.id
            ).count()
            
            # Lấy exam_type từ exam_instance hoặc blueprint
            exam_type_value = exam.exam_type
            if not exam_type_value and exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_type_value = blueprint.exam_type if blueprint.exam_type else None
                except ExamBlueprint.DoesNotExist:
                    pass
            
            # Check if student has completed this exam
            exam_result = None
            if student_id:
                try:
                    # First, check all exam results for this student and exam (any status)
                    # Convert student_id to string to ensure matching
                    student_id_str = str(student_id)
                    exam_id_str = str(exam.id)
                    
                    all_results = ExamResult.objects.filter(
                        student_id=student_id_str,
                        exam_instance_id=exam_id_str
                    ).order_by('-submitted_at', '-created_at')
                    
                    logger.info(f"🔍 Checking exam results for student {student_id}, exam {exam.id}: found {all_results.count()} results")
                    for res in all_results:
                        logger.info(f"  - Result {res.id}: status={res.status}, score={res.score}, submitted_at={res.submitted_at}")
                    
                    # Priority 1: Get completed result (most recent)
                    exam_result = all_results.filter(status='completed').first()
                    
                    # Priority 2: If no completed result, check for any result with a score (might be graded)
                    if not exam_result:
                        exam_result = all_results.filter(score__isnull=False).exclude(score=0).first()
                        if exam_result:
                            logger.info(f"⚠️ Found exam result with score (status={exam_result.status}) for student {student_id}, exam {exam.id}: result_id={exam_result.id}, score={exam_result.score}")
                    
                    # Priority 3: If still no result, get the most recent one (might be in_progress)
                    # But only if we want to show "continue exam" instead of "start exam"
                    # For now, we only show completed exams, so skip this
                    
                    if exam_result:
                        logger.info(f"✅ Using exam result for student {student_id}, exam {exam.id}: result_id={exam_result.id}, status={exam_result.status}, score={exam_result.score}")
                    else:
                        logger.info(f"❌ No completed exam result found for student {student_id}, exam {exam.id}")
                except Exception as e:
                    logger.error(f"❌ Error checking exam result: {str(e)}", exc_info=True)
            
            exam_data = {
                'id': str(exam.id),
                'title': exam.title,
                'exam_type': exam_type_value or 'placement',
                'skill_group': skill_group,
                'status': exam.status,
                'total_questions': question_count,
                'has_completed': exam_result is not None,
                'exam_result_id': str(exam_result.id) if exam_result else None,
                'exam_result_score': float(exam_result.score) if exam_result and exam_result.score is not None else None,
                'exam_result_submitted_at': exam_result.submitted_at.isoformat() if exam_result and exam_result.submitted_at else None
            }
            
            logger.info(f"📊 Exam data for {exam.id}: has_completed={exam_data['has_completed']}, exam_result_id={exam_data['exam_result_id']}, score={exam_data['exam_result_score']}")
            
            # Thêm duration nếu có trong blueprint
            if exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_data['duration'] = getattr(blueprint, 'duration', None)
                except ExamBlueprint.DoesNotExist:
                    pass
            
            result.append(exam_data)
        
        return Response({
            'success': True,
            'data': result
        })
    
    @action(detail=False, methods=['get'], url_path='class-tests')
    def class_tests(self, request):
        """
        GET /api/tests/exam-instances/class-tests/?student_id={student_id}&exam_type={midterm|final}
        
        Lấy danh sách midterm hoặc final tests theo lớp của học sinh
        Học sinh phải có lớp mới được làm test giữa khóa và cuối khóa
        """
        student_id_param = request.query_params.get('student_id')
        exam_type_param = request.query_params.get('exam_type')  # 'midterm' hoặc 'final'
        
        if not student_id_param:
            return Response({
                'success': False,
                'error': 'student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if exam_type_param not in ['midterm', 'final']:
            return Response({
                'success': False,
                'error': 'exam_type must be "midterm" or "final"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🔍 Class tests API called: student_id={student_id_param}, exam_type={exam_type_param}")
        
        # Convert user_account_id to student_id if needed
        actual_student_id = None
        
        # If authenticated, try to get student from user account
        if request.user and request.user.is_authenticated:
            try:
                from users.models import Student
                student = Student.objects.filter(user_account_id=request.user.id).first()
                if student:
                    actual_student_id = student.id
                    logger.info(f"✅ Found student from authenticated user: {actual_student_id}")
            except Exception as e:
                logger.warning(f"Could not get student from authenticated user: {e}")
        
        # If not found from auth, try to use provided student_id_param
        if not actual_student_id and student_id_param:
            try:
                from users.models import Student
                student = Student.objects.filter(id=student_id_param).first()
                if not student:
                    student = Student.objects.filter(user_account_id=student_id_param).first()
                    if student:
                        logger.info(f"✅ Found student by user_account_id: {student_id_param} → {student.id}")
                if student:
                    actual_student_id = student.id
                    logger.info(f"✅ Found student from provided ID: {actual_student_id}")
                else:
                    logger.warning(f"❌ No student found for ID: {student_id_param}")
            except Exception as e:
                logger.error(f"Error converting student_id: {str(e)}", exc_info=True)
        
        if not actual_student_id:
            logger.warning(f"⚠️ Could not determine actual student_id, using provided: {student_id_param}")
            actual_student_id = student_id_param
        
        student_id = actual_student_id
        logger.info(f"📌 Using student_id: {student_id}")
        
        # Lấy danh sách lớp học của học sinh
        from enrollment.models import Enrollment
        enrollments = Enrollment.objects.filter(
            student_id=student_id,
            class_id__isnull=False  # Chỉ lấy enrollment có class_id (đã được gán lớp)
        )
        
        class_ids = [str(e.class_id) for e in enrollments if e.class_id]
        
        if not class_ids:
            logger.warning(f"⚠️ Student {student_id} has no classes enrolled")
            return Response({
                'success': True,
                'data': [],
                'message': 'Bạn chưa có lớp học. Vui lòng đăng ký lớp học trước khi làm bài test giữa khóa và cuối khóa.'
            })
        
        logger.info(f"📚 Student {student_id} is enrolled in {len(class_ids)} classes: {class_ids}")
        
        # Lọc exam instances với exam_type = 'midterm' hoặc 'final' và class_id trong danh sách lớp của học sinh
        published_exams = ExamInstance.objects.filter(
            status='published',
            class_id__in=class_ids  # Chỉ lấy exam của các lớp mà học sinh đang học
        ).order_by('title')
        
        # Filter exams có exam_type='midterm' hoặc 'final' (hoặc từ blueprint)
        class_exams = []
        for exam in published_exams:
            # Check exam_type từ exam_instance hoặc blueprint
            exam_type = exam.exam_type
            if not exam_type and exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_type = blueprint.exam_type if blueprint.exam_type else None
                except ExamBlueprint.DoesNotExist:
                    pass
            
            # Chỉ thêm nếu exam_type khớp với yêu cầu
            if exam_type == exam_type_param:
                class_exams.append(exam)
        
        logger.info(f"📋 Found {len(class_exams)} {exam_type_param} exams for student's classes")
        
        # Phân biệt LR và SW dựa vào title
        result = []
        for exam in class_exams:
            title_upper = exam.title.upper()
            skill_group = None
            
            if 'LISTENING' in title_upper or 'READING' in title_upper:
                skill_group = 'LR'
            elif 'SPEAKING' in title_upper or 'WRITING' in title_upper:
                skill_group = 'SW'
            
            # Lấy số câu hỏi từ exam instance questions
            question_count = ExamInstanceQuestion.objects.filter(
                exam_instance_id=exam.id
            ).count()
            
            # Lấy exam_type từ exam_instance hoặc blueprint
            exam_type_value = exam.exam_type
            if not exam_type_value and exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_type_value = blueprint.exam_type if blueprint.exam_type else None
                except ExamBlueprint.DoesNotExist:
                    pass
            
            # Lấy thông tin lớp học
            class_info = None
            if exam.class_id:
                try:
                    from classes.models import Class
                    cls = Class.objects.get(id=exam.class_id)
                    class_info = {
                        'id': str(cls.id),
                        'name': cls.name,
                        'course_name': None  # Có thể thêm nếu cần
                    }
                    # Lấy course name nếu có
                    if cls.course_id:
                        try:
                            from courses.models import Course
                            course = Course.objects.get(id=cls.course_id)
                            class_info['course_name'] = course.name
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Could not get class info for {exam.class_id}: {e}")
            
            # Check if student has completed this exam
            exam_result = None
            if student_id:
                try:
                    student_id_str = str(student_id)
                    exam_id_str = str(exam.id)
                    
                    all_results = ExamResult.objects.filter(
                        student_id=student_id_str,
                        exam_instance_id=exam_id_str
                    ).order_by('-submitted_at', '-created_at')
                    
                    # Priority 1: Get completed result (most recent)
                    exam_result = all_results.filter(status='completed').first()
                    
                    # Priority 2: If no completed result, check for any result with a score
                    if not exam_result:
                        exam_result = all_results.filter(score__isnull=False).exclude(score=0).first()
                    
                    if exam_result:
                        logger.info(f"✅ Found exam result for student {student_id}, exam {exam.id}: result_id={exam_result.id}, status={exam_result.status}, score={exam_result.score}")
                except Exception as e:
                    logger.error(f"❌ Error checking exam result: {str(e)}", exc_info=True)
            
            exam_data = {
                'id': str(exam.id),
                'title': exam.title,
                'exam_type': exam_type_value or exam_type_param,
                'skill_group': skill_group,
                'status': exam.status,
                'total_questions': question_count,
                'class_id': str(exam.class_id) if exam.class_id else None,
                'class_info': class_info,
                'has_completed': exam_result is not None,
                'exam_result_id': str(exam_result.id) if exam_result else None,
                'exam_result_score': float(exam_result.score) if exam_result and exam_result.score is not None else None,
                'exam_result_submitted_at': exam_result.submitted_at.isoformat() if exam_result and exam_result.submitted_at else None
            }
            
            # Thêm duration nếu có trong blueprint
            if exam.blueprint_id:
                try:
                    blueprint = ExamBlueprint.objects.get(id=exam.blueprint_id)
                    exam_data['duration'] = getattr(blueprint, 'duration', None)
                except ExamBlueprint.DoesNotExist:
                    pass
            
            result.append(exam_data)
        
        return Response({
            'success': True,
            'data': result
        })
    
    @action(detail=True, methods=['get', 'post'], url_path='start')
    def start_exam(self, request, pk=None):
        """Student starts exam - supports both GET and POST"""
        try:
            exam = self.get_object()
            
            # Get student_id - can be from query params, request data, or authenticated user
            student_id_param = request.query_params.get('student_id') or request.data.get('student_id')
            
            # If authenticated, try to get student from user account
            actual_student_id = None
            if request.user and request.user.is_authenticated:
                try:
                    from users.models import Student
                    # Try to get student by user_account
                    student = Student.objects.filter(user_account_id=request.user.id).first()
                    if student:
                        actual_student_id = student.id
                        logger.info(f"Found student from authenticated user: {actual_student_id}")
                except Exception as e:
                    logger.warning(f"Could not get student from authenticated user: {e}")
            
            # If not found from auth, try to use provided student_id
            # But first check if it's a valid student_id (exists in students table)
            if not actual_student_id and student_id_param:
                try:
                    from users.models import Student
                    # Check if student_id_param is a user_account_id or student_id
                    student = Student.objects.filter(id=student_id_param).first()
                    if not student:
                        # Try to find by user_account_id
                        student = Student.objects.filter(user_account_id=student_id_param).first()
                    if student:
                        actual_student_id = student.id
                        logger.info(f"Found student from provided ID: {actual_student_id}")
                except Exception as e:
                    logger.warning(f"Could not get student from provided ID: {e}")
            
            if not actual_student_id:
                return Response({
                    'detail': 'Không thể xác định học viên. Vui lòng đăng nhập lại hoặc cung cấp student_id hợp lệ.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            student_id = actual_student_id
            logger.info(f"Starting exam: exam_id={exam.id}, student_id={student_id}")
            
            # Check if student already has a result for this exam (any status)
            existing_result = ExamResult.objects.filter(
                student_id=student_id,
                exam_instance_id=exam.id
            ).first()
            
            if existing_result:
                logger.info(f"Found existing result: {existing_result.id}, status: {existing_result.status}")
                # If completed, return result with flag to show result page
                if existing_result.status == 'completed':
                    serializer = ExamResultSerializer(existing_result)
                    result_data = serializer.data
                    # Add flag to indicate exam is completed
                    if isinstance(result_data, dict):
                        result_data['already_completed'] = True
                    return Response(result_data)
                # If in_progress, return existing result
                serializer = ExamResultSerializer(existing_result)
                return Response(serializer.data)
            
            # Create new exam result
            # Since ExamResult has managed=False, we need to use raw SQL or handle it carefully
            logger.info(f"Creating new exam result for exam_id={exam.id}, student_id={student_id}")
            
            from django.db import connection
            from django.utils import timezone
            import uuid
            
            result_id = uuid.uuid4()
            now = timezone.now()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO exam_results 
                        (id, exam_instance_id, student_id, status, submitted_at, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        str(result_id),
                        str(exam.id),
                        str(student_id),
                        'in_progress',
                        now,
                        now,
                        now
                    ])
                
                # Get the created result
                result = ExamResult.objects.get(id=result_id)
                logger.info(f"Created exam result: {result.id}")
                serializer = ExamResultSerializer(result)
                return Response(serializer.data)
                
            except Exception as db_error:
                # Check if it's a unique constraint violation
                error_msg = str(db_error)
                if 'unique' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    logger.warning(f"Unique constraint violation, getting existing result")
                    # Get existing result
                    existing_result = ExamResult.objects.filter(
                        student_id=student_id,
                        exam_instance_id=exam.id
                    ).first()
                    if existing_result:
                        serializer = ExamResultSerializer(existing_result)
                        return Response(serializer.data)
                raise db_error
            
        except Exception as e:
            logger.error(f"Error starting exam: {str(e)}", exc_info=True)
            return Response({
                'detail': f'Lỗi khi bắt đầu bài test: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Exam Result Views
class ExamResultViewSet(viewsets.ModelViewSet):
    queryset = ExamResult.objects.all().order_by('-submitted_at')
    
    def _clean_text(self, text):
        """Clean text to handle encoding issues"""
        if text is None:
            return None
        try:
            # Try to decode if it's bytes
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='ignore')
            # Normalize unicode
            text = unicodedata.normalize('NFKC', str(text))
            # Remove null bytes
            text = text.replace('\x00', '')
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            logger.warning(f"Error cleaning text: {str(e)}")
            return str(text).encode('utf-8', errors='ignore').decode('utf-8')
    serializer_class = ExamResultSerializer

    def list(self, request, *args, **kwargs):
        """Override list method to add error handling"""
        try:
            logger.info("Fetching exam results list")
            # Use Django ORM with individual field handling
            queryset = ExamResult.objects.all().order_by('-submitted_at')
            results = []
            
            for obj in queryset:
                try:
                    # Create a clean representation with safe field access
                    result = {
                        'id': str(obj.id),
                        'student_id': str(obj.student_id) if obj.student_id else None,
                        'exam_instance_id': str(obj.exam_instance_id) if obj.exam_instance_id else None,
                        'status': obj.status,
                        'score': obj.score,
                        'submitted_at': obj.submitted_at,
                        'created_at': obj.created_at,
                        'updated_at': obj.updated_at,
                    }
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing exam result {obj.id}: {str(e)}")
                    # Add minimal data for problematic records
                    results.append({
                        'id': str(obj.id),
                        'student_id': str(obj.student_id) if obj.student_id else None,
                        'exam_instance_id': str(obj.exam_instance_id) if obj.exam_instance_id else None,
                        'status': obj.status,
                        'score': obj.score,
                        'submitted_at': obj.submitted_at,
                        'created_at': obj.created_at,
                        'updated_at': obj.updated_at,
                    })
            
            logger.info(f"Successfully fetched {len(results)} exam results")
            return Response(results)
                
        except Exception as e:
            logger.error(f"Error fetching exam results: {str(e)}")
            # Return empty list instead of error
            return Response([])

    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        """Submit answer for a question"""
        result = self.get_object()
        question_id = request.data.get('question_id')
        answer = request.data.get('answer')
        
        if not question_id or answer is None:
            return Response({'detail': 'question_id and answer are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update exam answer
        exam_answer, created = ExamAnswer.objects.get_or_create(
            result_id=result.id,
            question_id=question_id,
            defaults={'selected_answer': answer}
        )
        if not created:
            exam_answer.selected_answer = answer
            exam_answer.save(update_fields=['selected_answer'])
        
        return Response({'detail': 'Answer submitted successfully'})

    @action(detail=True, methods=['post'], url_path='finish')
    def finish_exam(self, request, pk=None):
        """Finish exam and calculate score"""
        try:
            try:
                result = self.get_object()
            except ExamResult.DoesNotExist:
                logger.error(f"Exam result not found: {pk}")
                return Response({
                    'detail': f'Không tìm thấy kết quả bài test với ID: {pk}'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error getting exam result: {str(e)}")
                return Response({
                    'detail': f'Lỗi khi lấy thông tin bài test: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Finishing exam result: {result.id}, current status: {result.status}")
            
            if result.status == 'completed':
                logger.warning(f"Exam result {result.id} already completed")
                return Response({
                    'detail': 'Exam already completed',
                    'exam_result_id': str(result.id)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate score
            correct_count = 0
            total_questions = 0
            
            # Get exam instance questions
            exam_questions = ExamInstanceQuestion.objects.filter(exam_instance_id=result.exam_instance_id)
            total_questions = exam_questions.count()
            
            logger.info(f"Exam has {total_questions} questions")
            
            if total_questions == 0:
                logger.warning(f"Exam instance {result.exam_instance_id} has no questions")
                return Response({
                    'detail': 'Exam instance không có câu hỏi. Không thể chấm điểm.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            for exam_question in exam_questions:
                try:
                    question = Question.objects.get(id=exam_question.question_id)
                    exam_answer = ExamAnswer.objects.filter(
                        result_id=result.id,
                        question_id=question.id
                    ).first()
                    
                    if exam_answer and exam_answer.selected_answer == question.correct_answer:
                        correct_count += 1
                        exam_answer.is_correct = True
                        exam_answer.save(update_fields=['is_correct'])
                    elif exam_answer:
                        exam_answer.is_correct = False
                        exam_answer.save(update_fields=['is_correct'])
                except Question.DoesNotExist:
                    logger.warning(f"Question {exam_question.question_id} not found")
                    continue
                except Exception as e:
                    logger.error(f"Error processing question {exam_question.question_id}: {str(e)}")
                    continue
            
            # Calculate score percentage
            score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            logger.info(f"Score calculated: {correct_count}/{total_questions} = {score_percentage}%")
            
            # Update result using raw SQL since model has managed=False
            from django.db import connection
            from django.utils import timezone
            
            now = timezone.now()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE exam_results 
                        SET score = %s, status = %s, submitted_at = %s, updated_at = %s
                        WHERE id = %s
                    """, [
                        float(score_percentage),
                        'completed',
                        now,  # Set submitted_at khi finish exam
                        now,
                        str(result.id)
                    ])
                
                logger.info(f"✅ Updated exam_result {result.id} in database")
            except Exception as db_error:
                logger.error(f"Error updating exam_result in database: {str(db_error)}")
                raise db_error
            
            # Get updated result - cannot use refresh_from_db with managed=False
            # So we'll manually update the object
            result.score = score_percentage
            result.status = 'completed'
            result.submitted_at = now  # Cập nhật submitted_at trong object
            result.updated_at = now
            
            logger.info(f"✅ Exam result {result.id} completed successfully. Score: {score_percentage}%")
            print(f"[FINISH_EXAM] ✅ Exam result {result.id} completed successfully. Score: {score_percentage}%")
            
            # Gọi hàm cập nhật StudentCertificate thủ công vì signal không trigger với raw SQL
            # (ExamResult có managed=False nên signal post_save không tự động chạy)
            logger.info(f"🔄 About to call update_student_certificate_from_exam_result for result {result.id}")
            print(f"[FINISH_EXAM] 🔄 About to call update_student_certificate_from_exam_result for result {result.id}")
            logger.info(f"📊 Result details: id={result.id}, student_id={result.student_id}, exam_instance_id={result.exam_instance_id}, status={result.status}, score={result.score}, submitted_at={result.submitted_at}")
            print(f"[FINISH_EXAM] 📊 Result details: id={result.id}, student_id={result.student_id}, exam_instance_id={result.exam_instance_id}, status={result.status}, score={result.score}, submitted_at={result.submitted_at}")
            try:
                update_student_certificate_from_exam_result(result)
                logger.info(f"✅ Successfully updated StudentCertificate for exam result {result.id}")
                print(f"[FINISH_EXAM] ✅ Successfully updated StudentCertificate for exam result {result.id}")
            except Exception as cert_error:
                logger.error(f"❌ ERROR updating StudentCertificate: {str(cert_error)}", exc_info=True)
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                print(f"[FINISH_EXAM] ❌ ERROR updating StudentCertificate: {str(cert_error)}")
                print(f"[FINISH_EXAM] ❌ Full traceback: {traceback.format_exc()}")
                # Không fail request nếu update certificate lỗi
            
            serializer = ExamResultSerializer(result)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error finishing exam: {str(e)}", exc_info=True)
            return Response({
                'detail': f'Lỗi khi chấm điểm: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_results(self, request, student_id=None):
        """Get student's test results"""
        results = ExamResult.objects.filter(student_id=student_id).order_by('-submitted_at')
        return Response(ExamResultSerializer(results, many=True).data)
    
    @action(detail=True, methods=['get'], url_path='answers')
    def get_exam_answers(self, request, pk=None):
        """Get all answers for an exam result"""
        try:
            try:
                result = self.get_object()
            except ExamResult.DoesNotExist:
                logger.error(f"Exam result not found: {pk}")
                return Response({
                    'detail': f'Không tìm thấy kết quả bài test với ID: {pk}'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error getting exam result: {str(e)}")
                return Response({
                    'detail': f'Lỗi khi lấy thông tin bài test: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Getting answers for exam result: {result.id}")
            
            # Get all exam answers for this result
            exam_answers = ExamAnswer.objects.filter(result_id=result.id)
            logger.info(f"Found {exam_answers.count()} exam answers")
            
            # Also get all questions from exam instance to show unanswered questions
            exam_questions = ExamInstanceQuestion.objects.filter(
                exam_instance_id=result.exam_instance_id
            ).order_by('order_number')
            
            answers_data = []
            answered_question_ids = set()
            
            # Process existing answers
            for exam_answer in exam_answers:
                try:
                    question = Question.objects.get(id=exam_answer.question_id)
                    answered_question_ids.add(str(question.id))
                    
                    question_group = None
                    if question.group_id:
                        try:
                            question_group = QuestionGroup.objects.get(id=question.group_id)
                        except QuestionGroup.DoesNotExist:
                            pass
                    
                    # Get order number from exam instance questions
                    exam_question = ExamInstanceQuestion.objects.filter(
                        exam_instance_id=result.exam_instance_id,
                        question_id=question.id
                    ).first()
                    
                    answer_data = {
                        'id': str(exam_answer.id),
                        'question_id': str(question.id),
                        'order_number': exam_question.order_number if exam_question else None,
                        'part': question.part,
                        'skill': question.skill,
                        'question_text': self._clean_text(question.text) if question.text else None,
                        'option_a': self._clean_text(question.option_a) if question.option_a else None,
                        'option_b': self._clean_text(question.option_b) if question.option_b else None,
                        'option_c': self._clean_text(question.option_c) if question.option_c else None,
                        'option_d': self._clean_text(question.option_d) if question.option_d else None,
                        'correct_answer': question.correct_answer,
                        'selected_answer': exam_answer.selected_answer,
                        'is_correct': exam_answer.is_correct,
                        'difficulty': question.difficulty,
                        'audio_file': question.audio_file,
                        'group_id': str(question.group_id) if question.group_id else None,
                        'group': None
                    }
                    
                    # Add group info if exists
                    if question_group:
                        answer_data['group'] = {
                            'id': str(question_group.id),
                            'part': question_group.part,
                            'skill': question_group.skill,
                            'context': self._clean_text(question_group.context) if question_group.context else None,
                            'audio_file': question_group.audio_file,
                            'image_file': question_group.image_file
                        }
                    
                    answers_data.append(answer_data)
                except Question.DoesNotExist:
                    logger.warning(f"Question {exam_answer.question_id} not found for answer {exam_answer.id}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing answer {exam_answer.id}: {str(e)}")
                    continue
            
            # Add unanswered questions
            for exam_question in exam_questions:
                if str(exam_question.question_id) not in answered_question_ids:
                    try:
                        question = Question.objects.get(id=exam_question.question_id)
                        question_group = None
                        if question.group_id:
                            try:
                                question_group = QuestionGroup.objects.get(id=question.group_id)
                            except QuestionGroup.DoesNotExist:
                                pass
                        
                        answer_data = {
                            'id': None,
                            'question_id': str(question.id),
                            'order_number': exam_question.order_number,
                            'part': question.part,
                            'skill': question.skill,
                            'question_text': self._clean_text(question.text) if question.text else None,
                            'option_a': self._clean_text(question.option_a) if question.option_a else None,
                            'option_b': self._clean_text(question.option_b) if question.option_b else None,
                            'option_c': self._clean_text(question.option_c) if question.option_c else None,
                            'option_d': self._clean_text(question.option_d) if question.option_d else None,
                            'correct_answer': question.correct_answer,
                            'selected_answer': None,
                            'is_correct': None,
                            'difficulty': question.difficulty,
                            'audio_file': question.audio_file,
                            'group_id': str(question.group_id) if question.group_id else None,
                            'group': None
                        }
                        
                        if question_group:
                            answer_data['group'] = {
                                'id': str(question_group.id),
                                'part': question_group.part,
                                'skill': question_group.skill,
                                'context': self._clean_text(question_group.context) if question_group.context else None,
                                'audio_file': question_group.audio_file,
                                'image_file': question_group.image_file
                            }
                        
                        answers_data.append(answer_data)
                    except Question.DoesNotExist:
                        logger.warning(f"Question {exam_question.question_id} not found")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing unanswered question {exam_question.question_id}: {str(e)}")
                        continue
            
            # Sort by order_number
            answers_data.sort(key=lambda x: x['order_number'] if x['order_number'] else 9999)
            
            logger.info(f"Returning {len(answers_data)} answers")
            
            return Response({
                'result_id': str(result.id),
                'exam_instance_id': str(result.exam_instance_id),
                'student_id': str(result.student_id),
                'score': float(result.score) if result.score is not None else None,
                'status': result.status,
                'submitted_at': result.submitted_at.isoformat() if result.submitted_at else None,
                'answers': answers_data
            })
            
        except Exception as e:
            logger.error(f"Error getting exam answers: {str(e)}", exc_info=True)
            return Response({
                'detail': f'Lỗi khi lấy câu trả lời: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Student Progress Views
class StudentProgressViewSet(viewsets.ModelViewSet):
    queryset = StudentProgress.objects.all().order_by('-updated_at')
    serializer_class = StudentProgressSerializer

    @action(detail=False, methods=['get'], url_path='(?P<student_id>[^/.]+)')
    def get_progress(self, request, student_id=None):
        """Get student progress"""
        try:
            progress = StudentProgress.objects.get(student_id=student_id)
            return Response(StudentProgressSerializer(progress).data)
        except StudentProgress.DoesNotExist:
            return Response({'detail': 'Student progress not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put'], url_path='(?P<student_id>[^/.]+)')
    def update_progress(self, request, student_id=None):
        """Update student progress"""
        try:
            progress = StudentProgress.objects.get(student_id=student_id)
        except StudentProgress.DoesNotExist:
            progress = StudentProgress.objects.create(student_id=student_id)
        
        serializer = self.get_serializer(progress, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# Entry Test View
class EntryTestViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='entry')
    def take_entry_test(self, request):
        """Student takes entry test"""
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create entry test result
        result = ExamResult.objects.create(
            student_id=student_id,
            exam_instance_id=None,  # Entry test doesn't use exam instance
            status='in_progress'
        )
        
        return Response({
            'result_id': result.id,
            'message': 'Entry test started. Use submit-answer and finish endpoints.'
        }, status=status.HTTP_201_CREATED)

