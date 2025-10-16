from rest_framework.routers import DefaultRouter
from .views import (
    QuestionGroupViewSet, QuestionViewSet, ExamBlueprintViewSet, 
    ExamRuleViewSet, ExamInstanceViewSet, ExamResultViewSet,
    StudentProgressViewSet, EntryTestViewSet
)

router = DefaultRouter()
router.register(r'question-groups', QuestionGroupViewSet, basename='question-group')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'exam-blueprints', ExamBlueprintViewSet, basename='exam-blueprint')
router.register(r'exam-rules', ExamRuleViewSet, basename='exam-rule')
router.register(r'exam-instances', ExamInstanceViewSet, basename='exam-instance')
router.register(r'exam-results', ExamResultViewSet, basename='exam-result')
router.register(r'student-progress', StudentProgressViewSet, basename='student-progress')
router.register(r'tests', EntryTestViewSet, basename='entry-test')

urlpatterns = router.urls

