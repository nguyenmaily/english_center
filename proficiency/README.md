# Chức năng: Hồ sơ Năng lực Tiếng Anh

## Tổng quan

Chức năng này cho phép học viên quản lý hồ sơ năng lực tiếng Anh của mình, bao gồm:
- Upload chứng chỉ TOEIC (với OCR tự động)
- Làm Placement Test
- Xem lịch sử và năng lực hiện tại

## Đã hoàn thành

### 1. Database
- ✅ SQL script tạo bảng `student_certificates` (`sql/create_student_certificates_table.sql`)
- ✅ Các enum types: `skill_group_enum`, `source_type_enum`, `certificate_status_enum`, `verification_method_enum`
- ✅ Indexes và constraints

### 2. Django Model
- ✅ Model `StudentCertificate` với đầy đủ fields và validation
- ✅ Methods: `calculate_expired_date_for_certificate()`, `calculate_expired_date_for_test()`
- ✅ Properties: `is_expired`, `is_current`

### 3. Permissions
- ✅ Permission `manage_proficiency_profile` đã được thêm vào `setup_auth_data.py`
- ✅ Gán permission cho role `student`

### 4. Serializers
- ✅ `StudentCertificateSerializer` - Serializer đầy đủ
- ✅ `StudentCertificateCreateSerializer` - Tạo mới chứng chỉ
- ✅ `PlacementTestResultSerializer` - Lưu kết quả placement test
- ✅ `ProficiencyProfileSerializer` - Profile tổng hợp

### 5. API Endpoints
- ✅ `GET /api/proficiency/profile/` - Lấy profile (highlight cards + history)
- ✅ `POST /api/proficiency/upload-certificate/` - Upload chứng chỉ (chưa có OCR)
- ✅ `POST /api/proficiency/placement-test-result/` - Lưu kết quả placement test
- ✅ `GET /api/proficiency/history/` - Lịch sử chứng chỉ

## Cần hoàn thành

### 1. Google Cloud Vision API Integration
- [ ] Setup Google Cloud Vision API credentials
- [ ] Tạo service account và download JSON key
- [ ] Cài đặt `google-cloud-vision` package
- [ ] Tạo utility function để gọi OCR API
- [ ] Xử lý lỗi và retry logic

### 2. OCR Matching Logic
- [ ] Trích xuất thông tin từ ảnh: total_score, skill_group, name, test_date
- [ ] So khớp với dữ liệu học viên nhập:
  - So sánh điểm số (cho phép sai số nhỏ)
  - So sánh ngày thi
  - So sánh tên học viên (với full_name trong user_accounts)
- [ ] Tính % khớp và quyết định:
  - Khớp > 90% → status = VERIFIED
  - Không khớp → status = PENDING

### 3. Auto Update Final Test Score
- [ ] Tạo signal hoặc helper function để tự động cập nhật khi có kết quả final test
- [ ] Liên kết với model `StudentProgress`
- [ ] Tạo bản ghi với `source_type = final_test`

## Hướng dẫn Setup Google Cloud Vision API

### Bước 1: Tạo Google Cloud Project
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Enable "Cloud Vision API"

### Bước 2: Tạo Service Account
1. Vào "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Đặt tên: `english-center-ocr`
4. Grant role: "Cloud Vision API User"
5. Tạo key (JSON) và download về máy

### Bước 3: Cài đặt Package
```bash
pip install google-cloud-vision
```

### Bước 4: Cấu hình Credentials
1. Lưu file JSON key vào `english_center/proficiency/google_vision_credentials.json` (hoặc path khác)
2. Thêm vào `.env` hoặc `settings.py`:
```python
GOOGLE_VISION_CREDENTIALS_PATH = 'path/to/credentials.json'
```

### Bước 5: Sử dụng trong Code
Xem file `ocr_utils.py` (sẽ tạo sau) để biết cách sử dụng.

## Cấu trúc Files

```
proficiency/
├── __init__.py
├── models.py              # StudentCertificate model
├── serializers.py          # Các serializers
├── views.py                # API views
├── urls.py                 # URL routing
├── admin.py
├── apps.py
├── tests.py
└── README.md               # File này

sql/
└── create_student_certificates_table.sql  # SQL script tạo bảng
```

## API Documentation

### GET /api/proficiency/profile/
Lấy hồ sơ năng lực tiếng Anh của học viên.

**Response:**
```json
{
  "success": true,
  "data": {
    "current_lr": {...},  // Chứng chỉ LR hiện tại (null nếu chưa có/hết hạn)
    "current_sw": {...},  // Chứng chỉ SW hiện tại (null nếu chưa có/hết hạn)
    "history": [...],     // Lịch sử các chứng chỉ VERIFIED
    "can_take_placement_test_lr": true,
    "can_take_placement_test_sw": false
  }
}
```

### POST /api/proficiency/upload-certificate/
Upload chứng chỉ TOEIC.

**Request Body:**
```json
{
  "skill_group": "LR",
  "score_1": 450,
  "score_2": 400,
  "total_score": 850,
  "test_date": "2024-01-15",
  "proof_image": "https://..."
}
```

### POST /api/proficiency/placement-test-result/
Lưu kết quả Placement Test.

**Request Body:**
```json
{
  "skill_group": "LR",
  "score_1": 450,
  "score_2": 400,
  "total_score": 850
}
```

### GET /api/proficiency/history/
Lấy lịch sử chứng chỉ.

**Query Params:**
- `skill_group`: "LR" hoặc "SW" (optional)
- `status`: "VERIFIED", "PENDING", "REJECTED" (optional, mặc định: VERIFIED)

## Notes

- Tất cả endpoints yêu cầu authentication và permission `manage_proficiency_profile`
- Chỉ role `student` mới có quyền truy cập
- Điểm LR: 0-990, điểm SW: 0-400
- Chứng chỉ: expired_date = test_date + 2 năm
- Test: expired_date = today + 6 tháng






