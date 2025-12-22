4.2. Màn hình: "Đăng ký lớp học"
Mô tả: Flow đăng ký lớp học (6 bước)

Flow chi tiết:

Bước 1: Kiểm tra điểm xác định trình độ
API Endpoint:

GET /api/users/students/my-level/
Logic:

Nếu có điểm → Chuyển Bước 2
Nếu chưa có điểm → Hiển thị màn "Chưa có điểm xác định trình độ"
Message: "Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp"
Button "Làm test" → Navigate đến màn "Test đầu vào"
Button "Cập nhật chứng chỉ" → Navigate đến màn "Cập nhật chứng chỉ"
Màn hình: "Cập nhật chứng chỉ"

API Endpoint:

POST /api/users/students/{student_id}/certificates/
Request Body:

{
  "certificate_type": "ielts", // ielts, toeic, toefl, cambridge, other
  "certificate_name": "IELTS Academic",
  "score": 6.5,
  "reading_score": 6.5,
  "listening_score": 7.0,
  "speaking_score": 6.0,
  "writing_score": 6.5,
  "image_url": "https://...",
  "issued_date": "2024-01-01",
  "expiry_date": "2025-01-01",
  "notes": ""
}
Màn hình: "Test đầu vào"

API Endpoints:

# Lấy danh sách placement tests
GET /api/tests/exam-instances/placement-tests/?student_id={student_id}

# Bắt đầu làm test
POST /api/tests/exam-instances/{id}/start/?student_id={student_id}

# Nộp bài
POST /api/tests/exam-results/{id}/finish/
Bước 2: Chọn khóa học
API Endpoint:

GET /api/courses/courses/
Response:

{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "description": "...",
      "min_entry_score": 5.0,
      "is_eligible": true // dựa trên trình độ của học viên
    }
  ]
}
UI Components:

List hiển thị khóa học
Badge "Đủ điều kiện" / "Không đủ điều kiện"
Button "Đăng ký" (enable/disable theo is_eligible)
Click vào khóa học → Navigate đến màn "Chi tiết khóa học"
API Endpoint cho chi tiết khóa học:

GET /api/courses/courses/{id}/
Bước 3: Chọn lớp học
API Endpoint:

GET /api/courses/courses/{course_id}/eligible-classes/
Response:

{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate - Class A",
      "teacher_name": "Nguyễn Văn A",
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "current_student_count": 15,
      "limit_slot": 20,
      "status": "planned",
      "is_available": true // có slot và đã có giáo viên
    }
  ]
}
UI Components:

List hiển thị lớp học
Hiển thị số slot còn lại
Badge trạng thái
Button "Chọn lớp" (enable/disable theo is_available)
Click vào lớp → Navigate đến Bước 4
Bước 4: Xác nhận thông tin lớp
API Endpoint:

GET /api/classes/{id}/
UI Components:

Hiển thị thông tin lớp đầy đủ
Button "Thanh toán" → Navigate đến Bước 5
Bước 5: Thanh toán
API Endpoint:

POST /api/enrollment/enrollments/
Request Body:

{
  "class_id": "uuid",
  "payment_method": "cash" // hoặc "vnpay", "momo"
}
Response:

{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_status": "pending",
    "amount": 5000000,
    "due_date": "2024-01-17", // 2 ngày từ khi tạo
    "payment_url": "https://..." // nếu payment_method = vnpay/momo
  }
}
UI Components:

Radio buttons: Tiền mặt / VNPay / MoMo
Hiển thị số tiền
Hiển thị thời hạn thanh toán (2 ngày)
Button "Xác nhận thanh toán"
Nếu tiền mặt: Hiển thị thông báo "Vui lòng nộp tiền tại trung tâm"
Nếu VNPay/MoMo: Redirect đến payment gateway
API Endpoint cho payment callback:

GET /api/enrollment/payments/{gateway}/return/
POST /api/enrollment/payments/{gateway}/notify/
Bước 6: Hoàn thành đăng ký
UI Components:

Thông báo "Đăng ký lớp thành công!"
Button "Xem thời khóa biểu" → Navigate đến màn "Lịch học" hoặc hiển thị schedule ngay
API Endpoint để xem schedule ngay sau khi đăng ký:

GET /api/enrollment/enrollments/{enrollment_id}/schedule/
Response:

{
  "enrollment_id": "uuid",
  "class": {
    "id": "uuid",
    "name": "TOEIC Intermediate - Class A",
    "course": {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "level": "intermediate"
    },
    "teacher": {
      "id": "uuid",
      "name": "Nguyễn Văn A"
    },
    "campus": {
      "id": "uuid",
      "name": "Campus A"
    },
    "start_date": "2024-02-01",
    "end_date": "2024-05-01",
    "weekday": [2, 4, 6], // Thứ 3, 5, 7
    "time_slot": "18:00-20:00"
  },
  "schedule": {
    "by_week": [
      {
        "week": 1,
        "start_date": "2024-02-01",
        "end_date": "2024-02-07",
        "sessions": [
          {
            "id": "uuid",
            "study_date": "2024-02-01",
            "start_time": "18:00",
            "end_time": "20:00",
            "skill": null,
            "room": null,
            "teacher": {
              "id": "uuid",
              "name": "Nguyễn Văn A"
            }
          }
        ]
      }
    ],
    "by_date": [
      {
        "date": "2024-02-01",
        "sessions": [...]
      }
    ]
  },
  "summary": {
    "total_sessions": 36,
    "completed_sessions": 0,
    "upcoming_sessions": 36,
    "next_session": {
      "date": "2024-02-01",
      "start_time": "18:00",
      "end_time": "20:00",
      "skill": null,
      "room": null
    }
  },
  "note": "Sessions chưa được tạo trong database, schedule được tính toán dựa trên thông tin lớp" // (nếu sessions chưa có)
}
Lưu ý:

API này tự động tính toán schedule dựa trên thông tin lớp (weekday, time_slot, start_date, end_date) nếu sessions chưa được tạo trong database
Schedule sẽ hiển thị ngay sau khi đăng ký thành công, không cần chờ sessions được tạo

---

## CÁC CÂU HỎI CẦN LÀM RÕ

### Bước 1: Kiểm tra điểm xác định trình độ

**Q1:** API `GET /api/users/students/my-level/` chưa có trong codebase. API này nên:
- Trả về điểm hiện tại từ `StudentCertificate` (LR và SW)?
- Nếu chưa có điểm → trả về `null` hoặc `{}`?
- Response format cụ thể như thế nào? (Ví dụ: `{ "lr_score": 850, "sw_score": 300 }` hay `{ "has_level": false }`?)
-> answer : Đúng rồi , trả điểm hiện tại từ `StudentCertificate` , nếu không có hoặc đã hết hạn thì trả về null , khi trả về null thì sẽ gợi ý người dùng cập nhật chứng chỉ hoặc làm bài test đầu vào . Format trả về tuỳ bạn , miễn là đồng nhất và không bug

**Q2:** Logic "Nếu chưa có điểm":
- Kiểm tra cả 2 nhóm kỹ năng (LR và SW) hay chỉ cần 1 trong 2?
- Nếu học viên chỉ có LR hoặc chỉ có SW thì có được đăng ký không?
- Hay bắt buộc phải có cả 2?
-> answer : vấn đề này hoàn toàn do khoá học mà học viên chọn , nếu học viên chọn khoá học về kĩ năng LR thì sẽ check điểm của kĩ năng LR , nếu chưa có điểm thì yêu cầu cập nhật điểm về kĩ năng này -> có thể là cập nhật chứng chỉ hoặc làm bài kiểm tra đầu vào . SẼ KHÔNG CÓ CHUYỆN BẮT LÀM CẢ 2 ĐÂU NHÉ , CHỈ LÀM LIÊN QUAN ĐẾ KĨ NĂNG TRONG KHOÁ HỌC. 

**Q3:** API `POST /api/users/students/{student_id}/certificates/` trong file khác với endpoint hiện tại (`POST /api/proficiency/upload-certificate/`):
- Có cần tạo endpoint mới theo format trong file không?
- Hay dùng endpoint hiện có và điều chỉnh frontend?
- Request body trong file có format khác (IELTS/TOEIC/TOEFL) so với model hiện tại (chỉ TOEIC LR/SW)?
-> answer: dùng endpoint hiện có nhé , request body trong file để như hiện tại (TOEIC LR/SW) . 

**Q4:** API `GET /api/tests/exam-instances/placement-tests/?student_id={student_id}`:
- Cần tạo endpoint này mới?
- Logic: lọc `ExamInstance` với `exam_type = 'placement'`?
- Có cần phân biệt placement test cho LR và SW không? (2 bài test riêng biệt)
-> answer: Việc cần tạo endpoint mới không thi bạn hãy check trong codebase tests xem có endpoint với chức năng tương đương khôgn . 
Logic: lọc `ExamInstance` với `exam_type = 'placement'
cần phân biệt placement test cho LR và SW vò có 2 bài test riêng biệt 

**Q5:** Sau khi hoàn thành placement test:
- Kết quả tự động cập nhật vào `StudentCertificate` qua signal?
- Hay cần gọi API `POST /api/proficiency/placement-test-result/` riêng?
-> answer: sau khi hoàn thành placement test , điểm sẽ tự động cập nhật vào `StudentCertificate` qua signal

### Bước 2: Chọn khóa học

**Q6:** Field `is_eligible` trong response:
- Logic tính `is_eligible` dựa trên `min_entry_score` của course so với điểm của học viên?
- So sánh với điểm nào? (LR, SW, hay cả 2? Hay điểm nào cao hơn?)
- Nếu course không có `min_entry_score` → `is_eligible = true`?
- Hay cần gọi API `POST /api/proficiency/placement-test-result/` riêng?
-> answer: Đầu viên mỗi khoá học sẽ có gán tới skill ( course có skill_id ) , chúng ta sẽ lấy skil từ đây , sau đó về `StudentCertificate` để lấy điểm của học viên và check với `min_entry_score` của course . Nếu course không có `min_entry_score` → `is_eligible = true`

**Q7:** Trong file có `min_entry_score: 5.0` (float) nhưng trong model `Course` hiện tại là `min_entry_score` (Integer). 
- Có cần thay đổi kiểu dữ liệu không?
- Có cần thêm `max_entry_score` không?
-> answer: không cần thay đâu , có chút nhầm lẫn đó min_entry_score và `max_entry_score là integer 

**Q8:** Response format:
- API hiện tại trả về format nào? Có cần wrap trong `{ "success": true, "data": [...] }` không?
-> answer: Format hoàn toàn do bạn quyết định , miễn không bug 

### Bước 3: Chọn lớp học

**Q9:** API `GET /api/courses/courses/{course_id}/eligible-classes/` chưa có. Logic "eligible" bao gồm:
- Lớp thuộc course đó?
- `status = 'planned'` hoặc `'ongoing'`?
- `is_available = true` khi nào? (có slot + có giáo viên?)
- Có cần lọc theo campus không?
-> answer: lớp thuộc về course đó có status là planned và có teacher_id , và còn slot (current_student_count < limit_slot ) . Cho phép học viên filter theo campus . 

**Q10:** Field `is_available` trong response:
- `true` khi: `current_student_count < limit_slot` VÀ `teacher is not None`?
- Nếu `limit_slot = null` → coi là không giới hạn (luôn `is_available = true` nếu có giáo viên)?
-> answer: đúng rồi 

**Q11:** Response có cần thêm thông tin gì không? (ví dụ: `fee`, `campus_name`, `teacher_name`)
có nhé 

### Bước 4: Xác nhận thông tin lớp

**Q12:** API `GET /api/classes/{id}/` đã có. Có cần thêm thông tin gì cho bước xác nhận không? 
- Ví dụ: `fee` từ course, thông tin thanh toán, số slot còn lại?
-> answer: `fee` từ course, thông tin thanh toán, số slot , tên giáo viên 

### Bước 5: Thanh toán

**Q13:** API `POST /api/enrollment/enrollments/` đã có nhưng chưa hỗ trợ `payment_method`:
- Cần thêm field `payment_method` vào request body?
- Logic xử lý:
  - `cash` → `invoice_status = 'pending'`, `due_date = today + 2 ngày`?
  - `vnpay`/`momo` → tạo payment URL và redirect?
- `amount` lấy từ đâu? (từ `course.fee` hay `class.fee`?)
-> answer: 
- `cash` → `invoice_status = 'pending'`, `due_date = today + 2 ngày`
  - `vnpay`/`momo` → tạo payment URL và redirect
- `amount` lấy từ đâu? từ `course.fee'

**Q14:** Payment gateway (VNPay/MoMo):
- Đã tích hợp chưa? Nếu chưa, có cần implement không?
- Response có `payment_url` khi `payment_method = vnpay/momo`:
  - URL này được tạo từ đâu? (payment gateway API?)
  - Cần credentials/config nào?
-> answer: Payment gateway lấy là VNPay thôi nhé , chưa implement đâu . bạn giúp tôi nhé . NHớ tạo 1 file md để viết chi tiết cách thức implement ( cho tôi đọc hiểu ) và hướng dẫn tôi cài đặt nếu cần 

**Q15:** Callback URLs (`/api/enrollment/payments/{gateway}/return/` và `/notify/`):
- Đã có chưa?
- Logic xử lý callback như thế nào? (cập nhật `invoice_status = 'paid'`?)
-> answer: chưa có gì cả ... 

### Bước 6: Hoàn thành đăng ký - Schedule

**Q16:** API `GET /api/enrollment/enrollments/{enrollment_id}/schedule/` chưa có:
- Logic tính schedule:
  - Nếu sessions đã có trong DB → lấy từ `Session`?
  - Nếu chưa có → tính từ `weekday`, `time_slot`, `start_date`, `end_date` của class?
- Format response: `by_week` và `by_date` - có cần cả 2 không? Hay chỉ 1 trong 2?
-> answer: HIỆN TẠI TÔI KHÔNG RÕ LÀ SESSIONS SẼ DC TẠO NGAY KHI ĐĂNG KÝ THÀNG CÔNG HAY LÀ SESSION CHỈ CÓ KHI LỚP HỌC ĐÓ ĐANG VÀ ĐÃ DIỄN RA KHÔNG ? vÌ CÒN ẢNH HƯỞNG ĐẾN ĐIỂM DANH VÀ BÀI TẬP , BẠN CÓ THỂ XEM CODEBASE như nào và cho đưa ra logic hợp lí cho tôi nhé  
Format response: `by_week`

**Q17:** Trong response có `summary` với `next_session`:
- `next_session` là session đầu tiên có `study_date >= today`? Great 
- Nếu không có session nào sắp tới → `next_session = null`? Great 
- `completed_sessions` và `upcoming_sessions` tính như thế nào? (dựa trên `study_date` so với `today`?)
-> answer: - `completed_sessions` và `upcoming_sessions` tính  (dựa trên `study_date` so với `today

**Q18:** Field `note` trong response:
- Khi nào hiển thị note "Sessions chưa được tạo trong database..."?
- Có cần thêm note khác không?
-> answer: không cần đâu , bỏ   đi 

### Permissions & Authentication

**Q19:** Tất cả các API trong flow này:
- Chỉ dành cho student (role = 'student')?
- Cần permission cụ thể nào không? (ví dụ: `manage_enrollment`, `view_courses`)
- Có cần kiểm tra `student_id` từ token/user hay từ query param?
-> answer: hầu hết sẽ chỉ mình củ student nhưng có 1 vài cái là có thể của mọi người như  , `view_courses , check lại permission để gán permission hợp lí và tạo thêm nếu cần 

### Tổng hợp

**Q20:** Có cần thêm validation nào khác không?
- Ví dụ: Kiểm tra học viên đã đăng ký lớp này chưa? (tránh duplicate enrollment)
- Kiểm tra lớp đã bắt đầu chưa? (có cho phép đăng ký lớp đã `ongoing` không?)
-> answer : học viên có thể đăng ký 1 khoá học nhiều lần , không cần validation , học viên không thể đăng ký lớp học đang và đã diễn ra ( ongoing , fisnished , canceled )