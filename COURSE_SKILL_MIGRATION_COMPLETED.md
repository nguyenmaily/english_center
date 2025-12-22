# ✅ HOÀN THÀNH: Migration Course-Skill Relationship

## TỔNG QUAN

Đã hoàn thành việc đổi quan hệ giữa Course và Skill:
- **Trước:** `Skill.course_id` → 1 Course có nhiều Skills
- **Sau:** `Course.skill_id` → 1 Course có 1 Skill

---

## CÁC THAY ĐỔI ĐÃ THỰC HIỆN

### 1. ✅ Database Migration Script
**File:** `sql/migrate_course_skill_relationship.sql`

Script SQL để:
- Thêm `skill_id` vào bảng `courses`
- Migrate dữ liệu từ `skills.course_id` sang `courses.skill_id`
- Xóa `course_id` khỏi bảng `skills`
- Có rollback script nếu cần

**⚠️ QUAN TRỌNG:** Backup database trước khi chạy!

### 2. ✅ Models (Django)
**File:** `courses/models.py`

**Course Model:**
- ✅ Thêm field `skill` (ForeignKey đến Skill)
- ✅ `null=True, blank=True` (có thể null)
- ✅ `related_name='courses'` (1 skill có nhiều courses)

**Skill Model:**
- ✅ Xóa field `course` (ForeignKey)
- ✅ Thêm property `skill_group` để xác định LR/SW từ `skill.name`
- ✅ Cập nhật `__str__` method

### 3. ✅ Serializers
**File:** `courses/serializers.py`

**SkillSerializer:**
- ✅ Xóa `course_name`
- ✅ Thêm `courses_count` (số courses sử dụng skill)
- ✅ Thêm `skill_group` (LR/SW)

**CourseSerializer:**
- ✅ Xóa `skills_count`
- ✅ Thêm `skill` (SkillSerializer, read_only)
- ✅ Thêm `skill_id` (write_only, để assign skill)

**CourseDetailSerializer:**
- ✅ Xóa `skills` (list)
- ✅ Thêm `skill` (single object)
- ✅ Thêm `skill_id` (write_only)

### 4. ✅ Views
**File:** `courses/views.py`

**Đã xóa:**
- ❌ `CourseSkillsListView` (GET /api/courses/{course_id}/skills/)
- ❌ `CourseSkillsCreateView` (POST /api/courses/{course_id}/skills/create/)

**Đã thêm:**
- ✅ `CourseSkillView` (GET /api/courses/{course_id}/skill/)
- ✅ `CourseAssignSkillView` (PATCH /api/courses/{course_id}/assign-skill/)

### 5. ✅ URLs
**File:** `courses/urls.py`

**Đã thay đổi:**
- ❌ Xóa: `courses/<uuid:course_id>/skills/`
- ❌ Xóa: `courses/<uuid:course_id>/skills/create/`
- ✅ Thêm: `courses/<uuid:course_id>/skill/`
- ✅ Thêm: `courses/<uuid:course_id>/assign-skill/`

---

## HƯỚNG DẪN THỰC HIỆN

### Bước 1: Backup Database
```bash
# Backup PostgreSQL database
pg_dump -U your_user -d your_database > backup_before_migration.sql
```

### Bước 2: Chạy Migration SQL
```bash
# Kết nối PostgreSQL
psql -U your_user -d your_database

# Chạy migration script
\i sql/migrate_course_skill_relationship.sql
```

Hoặc chạy từng bước trong script để kiểm tra.

### Bước 3: Verify Data
Sau khi chạy migration, kiểm tra dữ liệu:

```sql
-- Kiểm tra courses có skill_id
SELECT COUNT(*) as total_courses,
       COUNT(skill_id) as courses_with_skill,
       COUNT(*) - COUNT(skill_id) as courses_without_skill
FROM courses;

-- Kiểm tra quan hệ 1-nhiều (1 skill có nhiều courses)
SELECT s.id, s.name, COUNT(c.id) as courses_count
FROM skills s
LEFT JOIN courses c ON c.skill_id = s.id
GROUP BY s.id, s.name
ORDER BY courses_count DESC;
```

### Bước 4: Test API

**Test GET course skill:**
```bash
GET /api/courses/{course_id}/skill/
```

**Test assign skill:**
```bash
PATCH /api/courses/{course_id}/assign-skill/
Body: {"skill_id": "uuid"}
```

**Test remove skill:**
```bash
PATCH /api/courses/{course_id}/assign-skill/
Body: {"skill_id": null}
```

---

## BREAKING CHANGES

### API Changes

**1. GET /api/courses/{course_id}/skills/** → ❌ Đã xóa
- **Thay thế:** GET /api/courses/{course_id}/skill/ (trả về 1 skill, không phải list)

**2. POST /api/courses/{course_id}/skills/create/** → ❌ Đã xóa
- **Thay thế:** PATCH /api/courses/{course_id}/assign-skill/ (assign skill cho course)

**3. Response format thay đổi:**
- **Trước:** `{"skills": [...], "skills_count": 2}`
- **Sau:** `{"skill": {...}, "skill_id": "uuid"}`

### Frontend Impact

Nếu frontend đang sử dụng:
- `GET /api/courses/{course_id}/skills/` → Cần đổi sang `/skill/`
- `POST /api/courses/{course_id}/skills/create/` → Cần đổi sang `/assign-skill/`
- Response `skills: []` → Cần đổi sang `skill: {}`

---

## LOGIC NGHIỆP VỤ MỚI

### Lấy skill từ course
```python
# Trước:
course = Course.objects.get(id=course_id)
skill = course.skills.first()  # Lấy skill đầu tiên

# Sau:
course = Course.objects.get(id=course_id)
skill = course.skill  # Trực tiếp
```

### Xác định skill_group từ skill
```python
# Skill model có property skill_group
skill = Skill.objects.get(id=skill_id)
skill_group = skill.skill_group  # 'LR' hoặc 'SW'

# Hoặc từ course
course = Course.objects.get(id=course_id)
if course.skill:
    skill_group = course.skill.skill_group
```

### Logic trong đăng ký lớp học
Theo yêu cầu trong `dangkylohoc.md`:
```python
# Lấy skill từ course
course = Course.objects.get(id=course_id)
skill = course.skill

# Xác định skill_group để check điểm học viên
if skill:
    skill_group = skill.skill_group  # 'LR' hoặc 'SW'
    # Lấy điểm từ StudentCertificate với skill_group này
    student_score = StudentCertificate.objects.filter(
        student=student,
        skill_group=skill_group,
        status='VERIFIED',
        expired_date__gte=today
    ).first()
```

---

## ROLLBACK (Nếu cần)

Nếu cần rollback, sử dụng script trong file `sql/migrate_course_skill_relationship.sql` (phần ROLLBACK SCRIPT).

Hoặc chạy:
```sql
BEGIN;

-- Thêm lại course_id vào skills
ALTER TABLE skills 
ADD COLUMN course_id UUID REFERENCES courses(id);

-- Migrate dữ liệu ngược lại
UPDATE skills s
SET course_id = (
    SELECT c.id 
    FROM courses c 
    WHERE c.skill_id = s.id 
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 FROM courses c WHERE c.skill_id = s.id
);

-- Xóa skill_id khỏi courses
ALTER TABLE courses DROP COLUMN IF EXISTS skill_id;

COMMIT;
```

Sau đó revert code Django về version cũ.

---

## KIỂM TRA SAU KHI DEPLOY

1. ✅ Kiểm tra courses có skill_id đúng không
2. ✅ Kiểm tra API endpoints hoạt động
3. ✅ Kiểm tra logic đăng ký lớp học (dangkylohoc.md)
4. ✅ Kiểm tra không có lỗi trong logs
5. ✅ Test frontend (nếu có)

---

## NOTES

- **skill_id có thể NULL:** Course có thể không có skill (tạm thời)
- **1 skill có nhiều courses:** Skill có thể được dùng bởi nhiều courses
- **skill_group:** Được xác định từ `skill.name` (property trong Skill model)
- **Session model:** Không thay đổi, vẫn có `skill_id`

---

## NEXT STEPS

Sau khi migration thành công:
1. ✅ Test tất cả API endpoints
2. ✅ Update frontend (nếu có)
3. ✅ Update documentation
4. ✅ Monitor production logs

---

**Ngày hoàn thành:** [Ngày hiện tại]
**Người thực hiện:** AI Assistant
**Status:** ✅ Hoàn thành - Sẵn sàng deploy



