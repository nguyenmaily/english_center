import random
from datetime import datetime
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
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
            text_fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            for field in text_fields:
                if data.get(field):
                    data[field] = self._clean_text(data[field])
            return data
        except Exception as e:
            logger.error(f"Serialization error for question {instance.id}: {str(e)}")
            return {
                'id': str(instance.id),
                'group_id': str(instance.group_id) if instance.group_id else None,
                'text': self._clean_text(instance.text) if instance.text else None,
                'option_a': self._clean_text(instance.option_a) if instance.option_a else None,
                'option_b': self._clean_text(instance.option_b) if instance.option_b else None,
                'option_c': self._clean_text(instance.option_c) if instance.option_c else None,
                'option_d': self._clean_text(instance.option_d) if instance.option_d else None,
                'correct_answer': self._clean_text(instance.correct_answer) if instance.correct_answer else None,
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
    class Meta:
        model = ExamInstance
        fields = '__all__'


class ExamResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamResult
        fields = '__all__'


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
        """Override create method to handle encoding"""
        try:
            serializer = self.get_serializer(data=request.data)
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
            return Response(
                {'detail': f'Error creating question group: {str(e)}'}, 
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
                    SELECT id, group_id, text, option_a, option_b, option_c, 
                           option_d, correct_answer, difficulty, created_at, updated_at 
                    FROM questions 
                    ORDER BY created_at DESC
                """)
                columns = [col[0] for col in cursor.description]
                results = []
                for row in cursor.fetchall():
                    try:
                        row_dict = dict(zip(columns, row))
                        # Clean text fields
                        for field in ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']:
                            if row_dict.get(field):
                                row_dict[field] = self._clean_text(row_dict[field])
                        results.append(row_dict)
                    except Exception as e:
                        logger.warning(f"Error processing row: {str(e)}")
                        # Add minimal data for problematic records
                        results.append({
                            'id': str(row[0]) if row[0] else None,
                            'group_id': str(row[1]) if row[1] else None,
                            'text': 'Error loading data',
                            'option_a': None,
                            'option_b': None,
                            'option_c': None,
                            'option_d': None,
                            'correct_answer': None,
                            'difficulty': row[8] if len(row) > 8 else None,
                            'created_at': row[9] if len(row) > 9 else None,
                            'updated_at': row[10] if len(row) > 10 else None,
                        })
                
                logger.info(f"Successfully fetched {len(results)} questions")
                return Response(results)
                
        except Exception as e:
            logger.error(f"Error fetching questions: {str(e)}")
            # Fallback to empty list if database has issues
            return Response([])
    
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
        """Override list method to add error handling"""
        try:
            logger.info("Fetching exam instances list")
            # Use Django ORM with individual field handling
            queryset = ExamInstance.objects.all().order_by('-generated_at')
            results = []
            
            for obj in queryset:
                try:
                    # Create a clean representation with safe field access
                    result = {
                        'id': str(obj.id),
                        'blueprint_id': str(obj.blueprint_id) if obj.blueprint_id else None,
                        'status': obj.status,
                        'generated_at': obj.generated_at,
                        'created_at': obj.created_at,
                        'updated_at': obj.updated_at,
                    }
                    
                    # Try to access text fields safely
                    try:
                        result['title'] = self._clean_text(obj.title) if obj.title else None
                    except Exception as e:
                        logger.warning(f"Error accessing title field for {obj.id}: {str(e)}")
                        result['title'] = 'Error loading data'
                    
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing exam instance {obj.id}: {str(e)}")
                    # Add minimal data for problematic records
                    results.append({
                        'id': str(obj.id),
                        'blueprint_id': str(obj.blueprint_id) if obj.blueprint_id else None,
                        'title': 'Error loading data',
                        'status': obj.status,
                        'generated_at': obj.generated_at,
                        'created_at': obj.created_at,
                        'updated_at': obj.updated_at,
                    })
            
            logger.info(f"Successfully fetched {len(results)} exam instances")
            return Response(results)
                
        except Exception as e:
            logger.error(f"Error fetching exam instances: {str(e)}")
            # Return empty list instead of error
            return Response([])
    
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
            status='published'
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(status='draft')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

