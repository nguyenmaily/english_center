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
            elif 'audio_file' not in data:
                data['audio_file'] = None
            
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
        exam = ExamInstance.objects.create(
            blueprint_id=blueprint_id,
            title=name,
            status='published',
            class_id=class_id  # Assign to class if provided
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
    
    @action(detail=True, methods=['get'], url_path='start')
    def start_exam(self, request, pk=None):
        """Student starts exam"""
        exam = self.get_object()
        student_id = request.query_params.get('student_id')
        
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if student already has a result for this exam
        existing_result = ExamResult.objects.filter(
            student_id=student_id,
            exam_instance_id=exam.id,
            status='in_progress'
        ).first()
        
        if existing_result:
            return Response(ExamResultSerializer(existing_result).data)
        
        # Create new exam result
        result = ExamResult.objects.create(
            student_id=student_id,
            exam_instance_id=exam.id,
            status='in_progress'
        )
        
        return Response(ExamResultSerializer(result).data)


# Exam Result Views
class ExamResultViewSet(viewsets.ModelViewSet):
    queryset = ExamResult.objects.all().order_by('-submitted_at')
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
        result = self.get_object()
        
        if result.status == 'completed':
            return Response({'detail': 'Exam already completed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate score
        correct_count = 0
        total_questions = 0
        
        # Get exam instance questions
        exam_questions = ExamInstanceQuestion.objects.filter(exam_instance_id=result.exam_instance_id)
        total_questions = exam_questions.count()
        
        for exam_question in exam_questions:
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
        
        # Update result
        result.score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        result.status = 'completed'
        result.save(update_fields=['score', 'status'])
        
        return Response(ExamResultSerializer(result).data)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_results(self, request, student_id=None):
        """Get student's test results"""
        results = ExamResult.objects.filter(student_id=student_id).order_by('-submitted_at')
        return Response(ExamResultSerializer(results, many=True).data)
    
    @action(detail=True, methods=['get'], url_path='answers')
    def get_exam_answers(self, request, pk=None):
        """Get all answers for an exam result"""
        result = self.get_object()
        
        # Get all exam answers for this result
        exam_answers = ExamAnswer.objects.filter(result_id=result.id)
        
        answers_data = []
        for exam_answer in exam_answers:
            try:
                question = Question.objects.get(id=exam_answer.question_id)
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
        
        # Sort by order_number
        answers_data.sort(key=lambda x: x['order_number'] if x['order_number'] else 9999)
        
        return Response({
            'result_id': str(result.id),
            'exam_instance_id': str(result.exam_instance_id),
            'student_id': str(result.student_id),
            'score': result.score,
            'status': result.status,
            'submitted_at': result.submitted_at,
            'answers': answers_data
        })


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

