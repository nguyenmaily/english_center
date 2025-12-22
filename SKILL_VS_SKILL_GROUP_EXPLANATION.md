# Giải thích: Skill vs Skill Group

## TÓM TẮT

**`skill`** và **`skill_group`** KHÔNG phải là một, nhưng có quan hệ với nhau:

- **`skill`**: Là một **Model** trong database (bảng `skills`) - một bản ghi cụ thể
- **`skill_group`**: Là một **giá trị được tính toán** từ `skill.name` → chỉ có 2 giá trị: `'LR'` hoặc `'SW'`

---

## 1. SKILL (Model trong Database)

### Định nghĩa
- **Bảng:** `skills`
- **Fields:** `id`, `name`, `description`, `created_at`, `updated_at`
- **Ví dụ records:**
  ```sql
  id: uuid-1, name: 'Listening-Reading', description: 'Kỹ năng Listening & Reading'
  id: uuid-2, name: 'Speaking-Writing', description: 'Kỹ năng Speaking & Writing'
  ```

### Trong Django Model
```python
class Skill(BaseModel):
    id = models.UUIDField(primary_key=True)
    name = models.TextField()  # Ví dụ: "Listening-Reading"
    description = models.TextField()
```

---

## 2. SKILL_GROUP (Giá trị tính toán)

### Định nghĩa
- **KHÔNG phải là Model riêng**
- **Là property** được tính từ `skill.name`
- **Chỉ có 2 giá trị:** `'LR'` hoặc `'SW'`

### Logic tính toán
```python
@property
def skill_group(self):
    """
    Xác định skill_group (LR/SW) từ skill.name
    """
    name_upper = self.name.upper()
    if 'LISTENING' in name_upper and 'READING' in name_upper:
        return 'LR'  # ← Giá trị này
    elif 'SPEAKING' in name_upper and 'WRITING' in name_upper:
        return 'SW'  # ← Giá trị này
    return None
```

### Ví dụ
```python
skill1 = Skill(name='Listening-Reading')
skill1.skill_group  # → 'LR'

skill2 = Skill(name='Speaking-Writing')
skill2.skill_group  # → 'SW'
```

---

## 3. SKILL_GROUP trong StudentCertificate

### Định nghĩa
- **Là một FIELD** trong bảng `student_certificates`
- **Lưu trữ giá trị:** `'LR'` hoặc `'SW'` (không phải skill_id)

### Trong Django Model
```python
class StudentCertificate(models.Model):
    class SkillGroup(models.TextChoices):
        LR = 'LR', 'Listening-Reading'
        SW = 'SW', 'Speaking-Writing'
    
    skill_group = models.CharField(
        max_length=2,
        choices=SkillGroup.choices,
        help_text='LR: Listening-Reading; SW: Speaking-Writing'
    )
    # ... các fields khác
```

### Ví dụ trong Database
```sql
student_id: uuid-123
skill_group: 'LR'  -- ← Lưu giá trị 'LR', không phải skill_id
total_score: 460
```

---

## 4. QUAN HỆ GIỮA SKILL VÀ SKILL_GROUP

### Flow logic:

```
1. Course có skill_id → tham chiếu đến bảng skills
   ↓
2. Skill có name = "Listening-Reading"
   ↓
3. Skill.skill_group property → tính toán từ name → trả về 'LR'
   ↓
4. StudentCertificate.skill_group → lưu giá trị 'LR' (không phải skill_id)
   ↓
5. So sánh: Course yêu cầu skill_group='LR' với StudentCertificate có skill_group='LR'
```

### Ví dụ cụ thể:

```python
# 1. Course có skill
course = Course.objects.get(name="BEGINNER'S TOEIC 350+")
course.skill  # → Skill(id=uuid-1, name='Listening-Reading')

# 2. Skill có skill_group property
course.skill.skill_group  # → 'LR' (tính từ name)

# 3. StudentCertificate lưu skill_group
cert = StudentCertificate.objects.get(student=student)
cert.skill_group  # → 'LR' (giá trị trong database)

# 4. So sánh để check eligibility
if course.skill.skill_group == cert.skill_group:
    # Cùng skill_group → có thể so sánh điểm
    if cert.total_score >= course.min_entry_score:
        return True  # Đủ điều kiện
```

---

## 5. TẠI SAO CẦN CẢ HAI?

### Skill (Model):
- ✅ Lưu thông tin chi tiết: name, description
- ✅ Có thể có nhiều skill khác nhau trong tương lai
- ✅ Dễ quản lý và mở rộng

### Skill Group (Giá trị):
- ✅ Đơn giản hóa: chỉ có 2 loại (LR/SW)
- ✅ Dễ so sánh và filter
- ✅ Phù hợp với cách chấm điểm TOEIC (LR: 0-990, SW: 0-400)

---

## 6. KẾT LUẬN

| Khía cạnh | Skill | Skill Group |
|-----------|-------|-------------|
| **Loại** | Model (bảng `skills`) | Property/Giá trị |
| **Số lượng** | Nhiều records | Chỉ 2 giá trị: 'LR', 'SW' |
| **Lưu trữ** | Database table | Tính toán từ `skill.name` |
| **Mục đích** | Quản lý thông tin chi tiết | So sánh và filter |

**Chúng KHÔNG phải là một**, nhưng:
- `skill` → có property `skill_group` → trả về `'LR'` hoặc `'SW'`
- `StudentCertificate` → có field `skill_group` → lưu `'LR'` hoặc `'SW'`

