# PHÂN TÍCH DỰ ÁN VÀ ƯỚC TÍNH THỜI GIAN

## 📊 TỔNG QUAN HIỆN TRẠNG

### 1. Database Structure Analysis

#### ✅ Các bảng đã có:
- **Authentication**: `user_accounts`, `roles`, `permissions`, `role_permissions`, `password_reset_tokens`
- **Users**: `students`, `teachers`, `managers`
- **Tests**: `question_groups`, `questions`, `exam_blueprints`, `exam_rules`, `exam_instances`, `exam_instance_questions`, `exam_results`, `exam_answers`, `student_progress`
- **Courses**: `courses`, `skills`
- **Classes**: `classes`
- **Sessions**: `sessions`
- **Enrollment**: `enrollments`, `payments`
- **Assignments**: `assignments`, `answer_keys`, `submissions`, `student_answers`
- **Campus**: `campuses`, `rooms`, `equipment`
- **Requests**: `leave_requests`, `reserve_requests`

#### ⚠️ Vấn đề phát hiện:

1. **Thiếu quan hệ giữa Placement Test và Course Selection**
   - `ExamResult` (placement test) không có quan hệ trực tiếp với `Course`
   - `StudentProgress.placement_score` tồn tại nhưng không được sử dụng để filter courses
   - Logic filter course theo `min_entry_score` đã có trong `courses/views.py` nhưng chưa tích hợp với placement test

2. **Thiếu model cho Certificate/Chứng chỉ**
   - Không có bảng lưu thông tin chứng chỉ của học viên
   - Không có model để upload và lưu hình ảnh chứng chỉ
   - Cần tạo: `StudentCertificate` model với fields: `student_id`, `certificate_type`, `certificate_name`, `image_url`, `issued_date`, `expiry_date`, `verification_status`

3. **Quan hệ Enrollment chưa hoàn chỉnh**
   - `Enrollment` có `student` và `class_field` ✅
   - Nhưng không có quan hệ với `Course` (chỉ có qua `class_field.course`)
   - Không có trường lưu placement test result được dùng để đăng ký

4. **Payment Gateway đã có nhưng chưa hoàn thiện**
   - VNPay và MoMo services đã được implement ✅
   - Callback handling đã có ✅
   - Nhưng thiếu: refund functionality, payment history UI, payment status tracking

---

## 🎯 CÔNG VIỆC CẦN LÀM

### 1. RÀ SOÁT DATABASE VÀ CODE (2-3 giờ)

#### Tasks:
- [ ] Kiểm tra tất cả foreign keys và relationships
- [ ] Xác định bảng thừa/thiếu
- [ ] Tạo migration cho `student_certificates` table
- [ ] Thêm index cho các trường thường query
- [ ] Review và fix các quan hệ thiếu

#### Files cần xem:
- Tất cả `models.py` files
- Migration files
- Database schema

---

### 2. XÂY DỰNG LẠI LUỒNG ĐĂNG KÝ (8-12 giờ)

#### Luồng hiện tại:
```
Register → Student Profile → [Manual] Enroll in Class → Payment
```

#### Luồng mới cần xây:
```
Register → Take Placement Test → View Recommended Courses → 
Select Course → Select Class → Create Enrollment → Payment → View Schedule
```

#### Tasks chi tiết:

**A. Placement Test Integration (2-3 giờ)**
- [ ] Tạo endpoint: `GET /api/tests/placement-tests/` - Lấy danh sách placement tests
- [ ] Tạo endpoint: `POST /api/tests/placement-tests/{id}/start` - Bắt đầu test
- [ ] Tạo endpoint: `POST /api/tests/placement-tests/{id}/submit` - Nộp bài
- [ ] Tự động cập nhật `StudentProgress.placement_score` sau khi hoàn thành test
- [ ] Tạo endpoint: `GET /api/students/{id}/placement-result` - Xem kết quả test

**B. Course Selection Based on Score (2-3 giờ)**
- [ ] Cải thiện `CourseListCreateView` để tự động filter theo placement score
- [ ] Tạo endpoint: `GET /api/courses/recommended?student_id={id}` - Lấy courses phù hợp
- [ ] Logic: Filter courses có `min_entry_score <= placement_score`
- [ ] Thêm endpoint: `GET /api/courses/{id}/eligible-classes?student_id={id}` - Lấy classes của course mà student có thể đăng ký

**C. Class Selection & Enrollment (2-3 giờ)**
- [ ] Cải thiện enrollment flow để check placement score requirement
- [ ] Validate: Student phải có placement score >= course.min_entry_score
- [ ] Tự động set `enrollment.amount = class.course.fee` nếu chưa có
- [ ] Tạo endpoint: `GET /api/enrollments/{id}/schedule` - Xem thời khóa biểu sau enrollment

**D. Payment Integration (1-2 giờ)**
- [ ] Đảm bảo payment flow hoạt động sau enrollment
- [ ] Tạo endpoint: `GET /api/enrollments/{id}/payment-status` - Check payment status
- [ ] Redirect sau payment thành công → hiển thị schedule

**E. Schedule View (1 giờ)**
- [ ] Cải thiện endpoint `my-classes` để hiển thị schedule đẹp hơn
- [ ] Group sessions theo ngày/tuần
- [ ] Thêm thông tin: room, teacher, skill

#### Files cần sửa/tạo:
- `tests/views.py` - Thêm placement test endpoints
- `courses/views.py` - Thêm recommended courses logic
- `enrollment/views.py` - Cải thiện enrollment flow
- `enrollment/serializers.py` - Thêm schedule serializer
- `users/models.py` - Có thể cần thêm methods

---

### 3. UPLOAD CHỨNG CHỈ (4-6 giờ)

#### Options cho file upload:

**Option 1: Django + Cloud Storage (Recommended)**
- **AWS S3** hoặc **Google Cloud Storage**
- **Pros**: Scalable, reliable, CDN support
- **Cons**: Cần setup account, có chi phí
- **Time**: 4-5 giờ

**Option 2: Django + Local Storage**
- Lưu file trong `MEDIA_ROOT`
- **Pros**: Đơn giản, không cần setup bên ngoài
- **Cons**: Không scalable, cần backup
- **Time**: 2-3 giờ

**Option 3: Third-party Services**
- **Cloudinary** (free tier: 25GB storage, 25GB bandwidth)
- **Imgur API** (free, nhưng không phù hợp cho production)
- **Firebase Storage** (free tier: 5GB)
- **Pros**: Dễ tích hợp, có free tier
- **Cons**: Phụ thuộc service bên ngoài
- **Time**: 3-4 giờ

#### Recommended: Cloudinary hoặc AWS S3

#### Tasks:
- [ ] Tạo model `StudentCertificate`
- [ ] Tạo migration cho `student_certificates` table
- [ ] Setup file upload (Cloudinary/S3/Local)
- [ ] Tạo serializer: `StudentCertificateSerializer`
- [ ] Tạo endpoints:
  - `POST /api/students/{id}/certificates/` - Upload certificate
  - `GET /api/students/{id}/certificates/` - List certificates
  - `GET /api/students/{id}/certificates/{cert_id}/` - Get certificate detail
  - `DELETE /api/students/{id}/certificates/{cert_id}/` - Delete certificate
- [ ] Validation: File type (jpg, png, pdf), file size (max 5MB)
- [ ] Image processing: Resize nếu cần

#### Files cần tạo/sửa:
- `users/models.py` - Thêm `StudentCertificate` model
- `users/serializers.py` - Thêm `StudentCertificateSerializer`
- `users/views.py` - Thêm certificate endpoints
- `users/urls.py` - Thêm certificate routes
- `english_center/settings.py` - Thêm file upload config

---

### 4. CÔNG CỤ THANH TOÁN (2-4 giờ)

#### Hiện trạng:
- ✅ VNPay service đã có
- ✅ MoMo service đã có
- ✅ Payment callback đã có
- ⚠️ Thiếu: Refund, Payment history UI, Payment status tracking tốt hơn

#### Tasks:
- [ ] Hoàn thiện refund functionality cho VNPay và MoMo
- [ ] Tạo endpoint: `POST /api/payments/{id}/refund` - Hoàn tiền
- [ ] Cải thiện payment status tracking
- [ ] Tạo endpoint: `GET /api/payments/statistics` - Thống kê thanh toán
- [ ] Thêm webhook handling cho payment notifications
- [ ] Testing với sandbox accounts

#### Files cần sửa:
- `enrollment/services/vnpay_service.py` - Implement refund
- `enrollment/services/momo_service.py` - Implement refund
- `enrollment/views.py` - Thêm refund endpoint, statistics

---

## ⏱️ ƯỚC TÍNH THỜI GIAN TỔNG THỂ

### Với sự hỗ trợ của AI (Auto):

| Công việc | Thời gian ước tính | Độ phức tạp |
|-----------|-------------------|-------------|
| 1. Rà soát database | **2-3 giờ** | Trung bình |
| 2. Xây dựng luồng đăng ký | **8-12 giờ** | Cao |
| 3. Upload chứng chỉ | **4-6 giờ** | Trung bình |
| 4. Công cụ thanh toán | **2-4 giờ** | Thấp-Trung bình |
| **TỔNG CỘNG** | **16-25 giờ** | |

### Breakdown chi tiết:

**Nếu làm full-time (8h/ngày):** 
- **2-3 ngày** để hoàn thành tất cả

**Nếu làm part-time (4h/ngày):**
- **4-6 ngày** để hoàn thành tất cả

**Nếu làm theo từng task:**
- Task 1: 1 buổi (2-3h)
- Task 2: 2-3 buổi (8-12h)
- Task 3: 1-2 buổi (4-6h)
- Task 4: 1 buổi (2-4h)

---

## 🎯 KHUYẾN NGHỊ THỨ TỰ THỰC HIỆN

### Phase 1: Foundation (Ưu tiên cao)
1. ✅ Rà soát database (2-3h)
2. ✅ Tạo model StudentCertificate (1h)
3. ✅ Setup file upload cơ bản (2h)

### Phase 2: Core Flow (Ưu tiên cao)
4. ✅ Placement test integration (2-3h)
5. ✅ Course selection based on score (2-3h)
6. ✅ Class selection & enrollment flow (2-3h)
7. ✅ Schedule view (1h)

### Phase 3: Enhancements (Ưu tiên trung bình)
8. ✅ Certificate upload UI/API (2-3h)
9. ✅ Payment improvements (2-4h)

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Database Migration**: Cần backup database trước khi chạy migration
2. **Testing**: Mỗi feature cần test kỹ trước khi deploy
3. **Payment Gateway**: Cần test với sandbox trước khi dùng production
4. **File Upload**: Cần setup storage (S3/Cloudinary) cho production
5. **API Documentation**: Nên document các endpoints mới

---

## 🚀 BẮT ĐẦU

Bạn muốn bắt đầu từ đâu? Tôi khuyến nghị:
1. **Bắt đầu với Task 1** (Rà soát database) - Để hiểu rõ structure
2. **Sau đó Task 2** (Luồng đăng ký) - Core functionality
3. **Tiếp theo Task 3** (Chứng chỉ) - Feature mới
4. **Cuối cùng Task 4** (Thanh toán) - Enhancement

Bạn có muốn tôi bắt đầu với Task 1 không?

Task 1: Rà soát database (2-3h) — hiểu rõ structure
Task 2: Luồng đăng ký (8-12h) — core functionality
Task 3: Upload chứng chỉ (4-6h) — feature mới
Task 4: Thanh toán (2-4h) — enhancement
Task 5 : Nghiên cứu luồng điểm danh 
