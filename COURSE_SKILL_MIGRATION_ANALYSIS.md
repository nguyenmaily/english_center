# PHÂN TÍCH THAY ĐỔI: Course.skill_id thay vì Skill.course_id

## TỔNG QUAN

**Thay đổi:** Đảo ngược quan hệ giữa Course và Skill
- **Hiện tại:** `Skill.course_id` → 1 Course có nhiều Skills
- **Mới:** `Course.skill_id` → 1 Course có 1 Skill

**Mức độ:** 🔴 **LỚN** - Thay đổi cấu trúc database và logic nghiệp vụ

---

## 1. THAY ĐỔI DATABASE

### 1.1. Cấu trúc hiện tại
```sql
-- Bảng skills
CREATE TABLE skills (
    id UUID PRIMARY KEY,
    name TEXT,
    description TEXT,
    course_id UUID REFERENCES courses(id)  -- ❌ Cần xóa
);

-- Bảng courses
CREATE TABLE courses (
    id UUID PRIMARY KEY,
    name TEXT,
    ...
    -- ❌ Chưa có skill_id
);
```

### 1.2. Cấu trúc mới
```sql
-- Bảng skills (giữ nguyên, chỉ xóa course_id)
CREATE TABLE skills (
    id UUID PRIMARY KEY,
    name TEXT,
    description TEXT
    -- ✅ Không còn course_id
);

-- Bảng courses (thêm skill_id)
CREATE TABLE courses (
    id UUID PRIMARY KEY,
    name TEXT,
    ...
    skill_id UUID REFERENCES skills(id)  -- ✅ Thêm mới
);
```

### 1.3. Migration SQL cần thực hiện

```sql
-- BƯỚC 1: Thêm skill_id vào courses (nullable tạm thời)
ALTER TABLE courses 
ADD COLUMN skill_id UUID REFERENCES skills(id);

-- BƯỚC 2: Migrate dữ liệu
-- Giả sử: lấy skill đầu tiên của mỗi course (hoặc logic khác)
UPDATE courses c
SET skill_id = (
    SELECT s.id 
    FROM skills s 
    WHERE s.course_id = c.id 
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 FROM skills s WHERE s.course_id = c.id
);

-- ⚠️ XỬ LÝ TRƯỜNG HỢP ĐẶC BIỆT:
-- - Course có nhiều skills → chọn skill nào? (skill đầu tiên? skill chính?)
-- - Course không có skill → skill_id = NULL? Hay bắt buộc phải có?
-- - Skill không thuộc course nào → xóa? Hay giữ lại?

-- BƯỚC 3: Xóa course_id khỏi skills
ALTER TABLE skills 
DROP COLUMN course_id;

-- BƯỚC 4: Set NOT NULL cho skill_id (nếu cần)
-- ALTER TABLE courses ALTER COLUMN skill_id SET NOT NULL;
```

**⚠️ RỦI RO:**
- Mất dữ liệu nếu course có nhiều skills (chỉ giữ lại 1)
- Cần quyết định logic chọn skill khi migrate
- Cần backup database trước khi chạy migration

---

## 2. THAY ĐỔI MODELS (Django)

### 2.1. Model Course
```python
# courses/models.py

class Course(BaseModel):
    # ... các field hiện tại ...
    skill = models.ForeignKey(
        'courses.Skill',
        on_delete=models.SET_NULL,  # hoặc RESTRICT
        null=True,
        blank=True,  # Có thể null không?
        related_name='courses',  # 1 skill có nhiều courses
        db_column='skill_id'
    )
```

### 2.2. Model Skill
```python
# courses/models.py

class Skill(BaseModel):
    # ... các field hiện tại ...
    # ❌ Xóa: course = models.ForeignKey(...)
    
    # ✅ Thêm related_name để truy cập ngược
    # (đã có trong Course.skill với related_name='courses')
```

---

## 3. THAY ĐỔI VIEWS

### 3.1. ❌ XÓA HOẶC SỬA: CourseSkillsListView
```python
# courses/views.py

# ❌ HIỆN TẠI:
class CourseSkillsListView(PermissionMixin, generics.ListAPIView):
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Skill.objects.filter(course_id=course_id)

# ✅ MỚI: Không còn cần endpoint này
# Hoặc đổi thành:
class CourseSkillView(PermissionMixin, generics.RetrieveAPIView):
    """GET /api/courses/{course_id}/skill/ - Lấy skill của course"""
    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        if course.skill:
            return Response(SkillSerializer(course.skill).data)
        return Response({'detail': 'Course has no skill'}, status=404)
```

### 3.2. ❌ XÓA HOẶC SỬA: CourseSkillsCreateView
```python
# courses/views.py

# ❌ HIỆN TẠI:
class CourseSkillsCreateView(PermissionMixin, generics.CreateAPIView):
    def perform_create(self, serializer):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        serializer.save(course=course)

# ✅ MỚI: Đổi thành assign skill cho course
class CourseAssignSkillView(PermissionMixin, APIView):
    """PATCH /api/courses/{course_id}/assign-skill/"""
    def patch(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        skill_id = request.data.get('skill_id')
        skill = get_object_or_404(Skill, pk=skill_id)
        course.skill = skill
        course.save()
        return Response({'detail': 'Skill assigned'})
```

### 3.3. ✅ GIỮ NGUYÊN: Các views khác
- `CourseListCreateView` - không ảnh hưởng
- `CourseDetailView` - cần sửa serializer
- `SkillDetailView` - không ảnh hưởng

---

## 4. THAY ĐỔI SERIALIZERS

### 4.1. CourseSerializer
```python
# courses/serializers.py

# ❌ HIỆN TẠI:
class CourseSerializer(serializers.ModelSerializer):
    skills_count = serializers.SerializerMethodField()
    
    def get_skills_count(self, obj):
        return obj.skills.count()  # ❌ Không còn obj.skills

# ✅ MỚI:
class CourseSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)  # ✅ Thay vì skills
    skill_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skill', 'skill_id'  # ✅ Thay skills_count bằng skill
        ]
```

### 4.2. CourseDetailSerializer
```python
# courses/serializers.py

# ❌ HIỆN TẠI:
class CourseDetailSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)  # ❌ List skills
    skills_count = serializers.SerializerMethodField()
    
    def get_skills_count(self, obj):
        return obj.skills.count()

# ✅ MỚI:
class CourseDetailSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)  # ✅ 1 skill
    skill_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skill', 'skill_id', 'classes_count', 'active_classes_count'
        ]
```

### 4.3. SkillSerializer
```python
# courses/serializers.py

# ❌ HIỆN TẠI:
class SkillSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'course', 'course_name']

# ✅ MỚI:
class SkillSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()  # ✅ Thay vì course_name
    
    def get_courses_count(self, obj):
        return obj.courses.count()  # ✅ Từ related_name='courses'
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'courses_count']
```

---

## 5. THAY ĐỔI LOGIC NGHIỆP VỤ

### 5.1. Logic lấy skill từ course
```python
# ❌ HIỆN TẠI:
course = Course.objects.get(id=course_id)
skill = course.skills.first()  # Lấy skill đầu tiên

# ✅ MỚI:
course = Course.objects.get(id=course_id)
skill = course.skill  # Trực tiếp
```

### 5.2. Logic trong đăng ký lớp học (dangkylohoc.md)
```python
# Theo yêu cầu trong dangkylohoc.md:
# "Đầu tiên mỗi khóa học sẽ có gán tới skill (course có skill_id)"

# ✅ Logic mới:
course = Course.objects.get(id=course_id)
skill = course.skill  # Lấy skill từ course

# Xác định skill_group từ skill
# Giả sử skill.name = "Listening-Reading" → skill_group = "LR"
# Hoặc có field skill_group trong Skill model?
```

### 5.3. Session model
```python
# class_sessions/models.py

# ✅ KHÔNG THAY ĐỔI
# Session vẫn có skill_id, không ảnh hưởng
class Session(BaseModel):
    skill = models.ForeignKey('courses.Skill', ...)  # ✅ Giữ nguyên
```

---

## 6. THAY ĐỔI URLs

### 6.1. courses/urls.py
```python
# ❌ XÓA:
path('courses/<uuid:course_id>/skills/', ...),
path('courses/<uuid:course_id>/skills/create/', ...),

# ✅ THÊM (nếu cần):
path('courses/<uuid:course_id>/skill/', views.CourseSkillView.as_view(), ...),
path('courses/<uuid:course_id>/assign-skill/', views.CourseAssignSkillView.as_view(), ...),
```

---

## 7. CÁC CÂU HỎI CẦN LÀM RÕ

### Q1: Logic migrate dữ liệu
- Nếu 1 course có nhiều skills → chọn skill nào?
  - Skill đầu tiên (theo thứ tự tạo)?
  - Skill có tên đặc biệt (ví dụ: "Main Skill")?
  - Skill được đánh dấu là "primary"?
  1 course có 1 skill thôi : LR hoặc SW 

### Q2: Ràng buộc dữ liệu
- `Course.skill_id` có thể `NULL` không?
  - Nếu có → Course có thể không có skill (tạm thời)
  - Nếu không → Bắt buộc mỗi course phải có skill
  có thể null 

### Q3: Quan hệ ngược
- 1 Skill có thể thuộc nhiều Courses không?
  - Nếu có → `related_name='courses'` (nhiều courses)
  - Nếu không → Cần unique constraint: `UNIQUE(skill_id)` trong courses
1 skill có thể ở nhiều course 

### Q4: Skill model
- Skill có cần thêm field `skill_group` (LR/SW) không?
  - Để map với `StudentCertificate.skill_group`
  - Hoặc lấy từ `skill.name`?
  Lấy từ skil.name nhé 

### Q5: Frontend/API compatibility
- Có cần giữ backward compatibility không?
  - API cũ trả về `skills: []` → API mới trả về `skill: {}`
  - Có cần versioning API không?
KHÔNG hiểu 
---

## 8. KẾ HOẠCH THỰC HIỆN

### Phase 1: Chuẩn bị
1. ✅ Backup database
2. ✅ Xác định logic migrate dữ liệu
3. ✅ Trả lời các câu hỏi ở mục 7

### Phase 2: Database Migration
1. ✅ Tạo migration SQL script
2. ✅ Test migration trên database dev/staging
3. ✅ Chạy migration trên production (có rollback plan)

### Phase 3: Code Changes
1. ✅ Sửa models (Course, Skill)
2. ✅ Sửa serializers
3. ✅ Sửa views
4. ✅ Sửa URLs
5. ✅ Update logic nghiệp vụ

### Phase 4: Testing
1. ✅ Unit tests
2. ✅ Integration tests
3. ✅ Manual testing
4. ✅ Frontend testing (nếu có)

### Phase 5: Deployment
1. ✅ Deploy code mới
2. ✅ Chạy migration
3. ✅ Verify data
4. ✅ Monitor errors

---

## 9. ĐÁNH GIÁ MỨC ĐỘ

### 🔴 MỨC ĐỘ: LỚN

**Lý do:**
1. ✅ Thay đổi cấu trúc database (ALTER TABLE)
2. ✅ Cần migrate dữ liệu (có rủi ro mất dữ liệu)
3. ✅ Thay đổi nhiều file code (models, views, serializers, URLs)
4. ✅ Thay đổi logic nghiệp vụ
5. ✅ Có thể ảnh hưởng frontend (nếu API response thay đổi)

**Thời gian ước tính:**
- Database migration: 2-4 giờ (bao gồm testing)
- Code changes: 4-6 giờ
- Testing: 2-4 giờ
- **Tổng: 8-14 giờ** (1-2 ngày làm việc)

**Rủi ro:**
- 🔴 **CAO**: Mất dữ liệu nếu migrate không đúng
- 🟡 **TRUNG BÌNH**: Breaking changes với frontend
- 🟡 **TRUNG BÌNH**: Logic nghiệp vụ có thể bị ảnh hưởng

---

## 10. KHUYẾN NGHỊ

### ✅ NÊN LÀM:
1. Backup database trước khi migrate
2. Test kỹ trên dev/staging trước
3. Có rollback plan
4. Document rõ logic migrate dữ liệu
5. Thông báo team về breaking changes

### ⚠️ CẦN CẨN THẬN:
1. Xử lý trường hợp course có nhiều skills
2. Xử lý trường hợp course không có skill
3. Đảm bảo không mất dữ liệu
4. Test kỹ logic nghiệp vụ sau khi thay đổi

### ❌ KHÔNG NÊN:
1. Chạy migration trực tiếp trên production
2. Bỏ qua testing
3. Không backup database

---

## 11. NEXT STEPS

Sau khi đọc phân tích này, vui lòng:
1. ✅ Trả lời các câu hỏi ở mục 7
2. ✅ Xác nhận logic migrate dữ liệu
3. ✅ Xác nhận ràng buộc (skill_id có thể NULL không?)
4. ✅ Xác nhận quan hệ (1 skill có thể thuộc nhiều courses không?)

Sau đó tôi sẽ:
- Tạo migration SQL script chi tiết
- Sửa code Django


