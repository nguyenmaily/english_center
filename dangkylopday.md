2.1. Màn hình chính: Danh sách lớp chưa có giáo viên
Mô tả:

Hiển thị danh sách các lớp học chưa được gán giáo viên và level <= level của giáo viên 
Giáo viên có thể chọn lớp muốn dạy và đăng ký
Có thể hủy đăng ký nếu lớp chưa có học viên đăng ký
UI Components:

Header: "ĐĂNG KÝ LỚP DẠY "
Search bar (tùy chọn)
Danh sách lớp:
Card mỗi lớp hiển thị:
Tên lớp
Tên khóa học
Ngày bắt đầu/kết thúc
Lịch học (weekday, time_slot)
Cơ sở
Số học viên hiện tại / Giới hạn
Button "Đăng ký"
Pull to refresh
API:

GET /api/users/teachers/available-classes/
Mô tả: Lấy danh sách lớp học chưa có giáo viên

Request:

Method: GET
Headers: Authorization: Bearer {token}
Response:

{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1",
      "course_name": "IELTS Foundation",
      "start_date": "2024-01-15",
      "end_date": "2024-04-15",
      "weekday": [2, 4, 6],
      "time_slot": "18:30-20:30",
      "campus": {
        "id": "uuid",
        "name": "Cơ sở Quận 1"
      },
      "current_student_count": 0,
      "limit_slot": 20
    }
  ]
}
2.2. Màn hình: Chi tiết lớp (trước khi đăng ký)
Mô tả:

Hiển thị thông tin chi tiết lớp học
Button "Đăng ký lớp này"
Hiển thị lịch học chi tiết
UI Components:

Header với nút back
Thông tin lớp chi tiết
Lịch học (tuần)
Button "Đăng ký lớp này" (primary)
Loading state khi đang đăng ký
API:

POST /api/users/teachers/register-class/
Mô tả: Đăng ký dạy lớp (có check trùng lịch)

Request:

Method: POST
Headers: Authorization: Bearer {token}
Body:
{
  "class_id": "uuid"
}
Response (Success):

{
  "success": true,
  "message": "Đăng ký lớp thành công",
  "data": {
    "class_id": "uuid",
    "class_name": "IELTS Foundation - Lớp 1"
  }
}
Response (Error - Trùng lịch):

{
  "success": false,
  "error": "Bạn đã có lớp vào thời gian này"
}
Response (Error - Lớp đã có giáo viên):

{
  "success": false,
  "error": "Class already has a teacher"
}
Response (Error - Trạng thái không hợp lệ):

{
  "success": false,
  "error": "Chỉ có thể đăng ký lớp ở trạng thái planned. Lớp hiện tại: ongoing"
}
Flow sau khi đăng ký thành công:

Hiển thị thông báo thành công
Tự động chuyển sang màn hình "LỊCH DẠY CỦA TÔI" (giống role Student)
2.3. Màn hình: Danh sách lớp đã đăng ký (để hủy)
Mô tả:

Hiển thị danh sách lớp giáo viên đã đăng ký
Chỉ hiển thị lớp chưa có học viên đăng ký
Có button "Hủy đăng ký"
UI Components:

Header: "LỚP ĐÃ ĐĂNG KÝ"
Danh sách lớp:
Card mỗi lớp
Button "Hủy đăng ký" (danger)
Hiển thị số học viên: "Chưa có học viên" hoặc "Đã có X học viên"
API:

POST /api/users/teachers/cancel-class-registration/
Mô tả: Hủy đăng ký lớp (chỉ được nếu lớp chưa có học viên)

Request:

Method: POST
Headers: Authorization: Bearer {token}
Body:
{
  "class_id": "uuid"
}
Response (Success):

{
  "success": true,
  "message": "Hủy đăng ký lớp thành công"
}
Response (Error - Đã có học viên):

{
  "success": false,
  "error": "Không thể hủy đăng ký vì lớp đã có 5 học viên đăng ký"
}

---

## CÂU HỎI CẦN LÀM RÕ - RÀNG BUỘC LEVEL

Để implement ràng buộc level (giáo viên chỉ có thể dạy các khóa học có level <= level của giáo viên), cần làm rõ các điểm sau:

### 1. Format và giá trị của Level

**Teacher Level:**
- Hiện tại có các giá trị: `junior`, `senior`, `expert`, `master`
- Lưu trong `Teacher.level` (TextField, có thể NULL)

**Course Level:**
- Lưu trong `Course.level` (TextField, có thể NULL)
- ❓ **Câu hỏi:** Course level có cùng format với Teacher level không? (cũng là `junior`, `senior`, `expert`, `master`?)
- ❓ **Câu hỏi:** Hay Course level có format khác? (ví dụ: `beginner`, `intermediate`, `advanced`, `expert`?)

### 2. Thứ tự so sánh Level

❓ **Câu hỏi:** Thứ tự so sánh level như thế nào?
- Có phải: `junior < senior < expert < master`?
- Ví dụ: Teacher `senior` có thể dạy Course `junior` và `senior`, nhưng không thể dạy `expert` và `master`?

❓ **Câu hỏi:** Nếu Course level và Teacher level khác format, làm sao map/so sánh?
- Ví dụ: Course `beginner` tương đương Teacher `junior`?

### 3. Trường hợp đặc biệt

**Trường hợp 1: Teacher không có level (NULL)**
- ❓ **Câu hỏi:** Teacher không có level có thể dạy tất cả courses, hay không được dạy course nào?
- ❓ **Câu hỏi:** Hay chỉ được dạy các course không có level (NULL)?

**Trường hợp 2: Course không có level (NULL)**
- ❓ **Câu hỏi:** Course không có level, teacher nào cũng có thể dạy, hay không ai được dạy?
- ❓ **Câu hỏi:** Hay chỉ teacher không có level mới được dạy?

**Trường hợp 3: Cả Teacher và Course đều không có level (NULL)**
- ❓ **Câu hỏi:** Trường hợp này có cho phép teacher đăng ký không?

### 4. Logic so sánh cụ thể

❓ **Câu hỏi:** Công thức so sánh chính xác là gì?
- `course.level <= teacher.level` (theo thứ tự định nghĩa)
- Hay có mapping table riêng?

### 5. Error message khi không đủ level

❓ **Câu hỏi:** Khi teacher cố đăng ký lớp có level cao hơn, error message như thế nào?
- Ví dụ: "Bạn không đủ trình độ để dạy khóa học này. Yêu cầu level: expert, level hiện tại của bạn: senior"
- Hay đơn giản: "Không đủ trình độ để dạy lớp này"

### 6. API Response cần bổ sung

❓ **Câu hỏi:** Trong response của `GET /api/users/teachers/available-classes/`, có cần hiển thị thêm:
- `course_level`: Level của khóa học
- `teacher_level`: Level của giáo viên hiện tại
- `is_level_eligible`: Boolean cho biết teacher có đủ level không?

---

**Vui lòng trả lời các câu hỏi trên để implement chính xác ràng buộc level.**

tôi muốn xây 1 khung ntlevel cho cả course cà teacher , 
`beginner`, `intermediate`, `advanced`, `expert`` , master
-> course có thể là 1 trong các level trên 
-> teacher sẽ là 1 trong 2 level : `expert` , master

thứ tự là beginner < intermediate`< `advanced`<  `expert`` < master
sẽ không có level null . 


Cần validation là lớp đăng ký phải không trùng lịch với các lớp hiện tại của giáo viên 
ví dụ : 
- giáo viên dạy kíp từ 2h-4h thứ 2,4,6 ngày 7/1/2025 - 7/3/2025 
thì có thể dăng kí tiếp : 4-6h thứ 2,4,6 ngày 7/1/2025 - 7/3/2025