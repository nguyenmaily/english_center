# PHÂN TÍCH SỐ MÀN HÌNH CẦN THIẾT CHO LUỒNG ĐĂNG KÝ

## 📱 TỔNG SỐ MÀN HÌNH: **7-8 MÀN HÌNH**

---

## 🎯 CHI TIẾT TỪNG MÀN HÌNH

### **Màn 1: Dashboard / Home (Sau khi đăng nhập)**
**Mục đích**: Điểm bắt đầu, kiểm tra trạng thái student

**Nội dung**:
- Chào mừng: "Chào mừng [Student Name]"
- Trạng thái placement test:
  - Nếu chưa có → Button lớn: "Làm Placement Test"
  - Nếu đã có → Hiển thị score + Button: "Xem khóa học phù hợp"
- Danh sách lớp đã đăng ký (nếu có)
- Quick links: My Classes, My Schedule, Profile

**API calls**:
- `GET /api/students/{id}/placement-result` (hoặc từ StudentProgress)
- `GET /api/enrollment/enrollments/my-classes/?student_id={id}`

**Navigation**:
- → Màn 2 (Nếu chưa có placement_score)
- → Màn 3 (Nếu đã có placement_score)

---

### **Màn 2: Placement Test**
**Mục đích**: Làm placement test

**Sub-screens** (có thể là modal hoặc separate screens):

#### 2A. Danh sách Placement Tests
**Nội dung**:
- Danh sách placement tests available
- Mỗi test hiển thị: Tên, Thời lượng, Số câu hỏi
- Button: "Bắt đầu làm test"

**API**: `GET /api/tests/exam-instances/placement-tests/?student_id={id}`

#### 2B. Làm Test (Full screen)
**Nội dung**:
- Timer countdown
- Câu hỏi hiện tại (1 câu/1 lần hoặc scroll)
- Options: A, B, C, D
- Progress bar: "Câu 5/50"
- Button: "Nộp bài"

**API**:
- `POST /api/tests/exam-instances/{id}/start?student_id={id}` - Bắt đầu
- `POST /api/tests/exam-results/{id}/submit-answer` - Submit từng câu
- `POST /api/tests/exam-results/{id}/finish` - Nộp bài

#### 2C. Kết quả Test
**Nội dung**:
- Điểm số lớn: "85.5 điểm"
- Thông báo: "Bạn đã hoàn thành placement test!"
- Button: "Xem khóa học phù hợp" → Navigate to Màn 3

**API**: Response từ `finish` đã có score

**Tổng**: 1 màn chính + 2-3 sub-screens = **1-2 màn** (tùy design)

---

### **Màn 3: Recommended Courses**
**Mục đích**: Xem danh sách courses phù hợp

**Nội dung**:
- Header: "Khóa học phù hợp với bạn" + Placement Score
- Danh sách courses:
  - Card mỗi course:
    - Tên, Level, Description
    - Match Score (% phù hợp) - Visual progress bar
    - Fee, Số sessions
    - Số classes available
    - Button: "Xem các lớp"
- Tab/Section: "Khóa học khác" (other_courses)

**API**: `GET /api/courses/recommended/?student_id={id}`

**Navigation**:
- Click "Xem các lớp" → Màn 4

**Tổng**: **1 màn**

---

### **Màn 4: Course Detail + Eligible Classes**
**Mục đích**: Xem chi tiết course và chọn lớp

**Layout**: 2 phần hoặc 2 tabs

#### Phần 1: Course Info (Top)
- Tên course, Level, Description
- Skills list
- Fee, Total sessions
- Requirements: min_entry_score

#### Phần 2: Eligible Classes List (Bottom/Scroll)
- Danh sách classes:
  - Card mỗi class:
    - Tên lớp
    - Schedule: Weekday, Time slot
    - Teacher: Tên, Specialization
    - Campus: Tên, Địa chỉ
    - Available slots: "Còn 5 chỗ"
    - Fee
    - Button: "Đăng ký lớp này"

**API**: `GET /api/courses/{course_id}/eligible-classes/?student_id={id}`

**Navigation**:
- Click "Đăng ký lớp này" → Màn 5

**Tổng**: **1 màn** (hoặc có thể tách thành 2 màn: Course Detail + Class List)

---

### **Màn 5: Enrollment Confirmation**
**Mục đích**: Xác nhận thông tin trước khi đăng ký

**Nội dung**:
- Summary card:
  - Course: Tên, Level
  - Class: Tên, Schedule
  - Teacher: Tên, Specialization
  - Campus: Tên, Địa chỉ
  - Fee: "5,000,000 VND"
  - Due date: "Hạn thanh toán: 10/01/2024"
- Schedule Preview (Collapsible):
  - Hiển thị 1-2 tuần đầu
  - Weekday, Time
- Checkbox: "Tôi đã đọc và đồng ý với điều khoản"
- Buttons:
  - "Hủy" → Quay lại Màn 4
  - "Xác nhận đăng ký" → Call API → Navigate to Màn 6

**API**: `POST /api/enrollment/enrollments/`

**Navigation**:
- Success → Màn 6 (Payment)
- Error → Hiển thị error message, ở lại màn này

**Tổng**: **1 màn**

---

### **Màn 6: Payment**
**Mục đích**: Thanh toán học phí

**Nội dung**:
- Thông tin thanh toán:
  - Enrollment ID
  - Số tiền: "5,000,000 VND"
  - Mô tả: "Thanh toán học phí - [Class Name]"
- Chọn phương thức thanh toán:
  - VNPay
  - MoMo
  - Tiền mặt (nếu có)
  - Chuyển khoản (nếu có)
- Button: "Thanh toán"

**API**: `POST /api/enrollment/enrollments/{id}/create-payment/`

**Flow**:
- Click "Thanh toán" → Call API → Nhận payment_url
- Redirect đến payment gateway (VNPay/MoMo)
- Sau khi thanh toán → Redirect về Màn 7

**Tổng**: **1 màn** (+ Payment Gateway external)

---

### **Màn 7: Enrollment Success + Schedule**
**Mục đích**: Hiển thị kết quả đăng ký thành công và schedule

**Nội dung**:
- Success message: "Đăng ký thành công!" (với icon checkmark)
- Thông tin enrollment:
  - Enrollment ID
  - Class name
  - Payment status
- Schedule View:
  - Tabs: "Theo tuần" / "Theo ngày"
  - Calendar view hoặc List view
  - Mỗi session hiển thị:
    - Date, Time
    - Room
    - Teacher
    - Skill
- Summary:
  - Total sessions: 30
  - Next session: "16/01/2024 - 08:00"
- Buttons:
  - "Xem thời khóa biểu đầy đủ" → Navigate to My Classes
  - "Quay về trang chủ" → Navigate to Màn 1

**API**: `GET /api/enrollment/enrollments/{id}/schedule/`

**Tổng**: **1 màn**

---

### **Màn 8: My Classes / My Schedule (Optional - có thể dùng chung với Màn 1)**
**Mục đích**: Xem tất cả classes và schedule của student

**Nội dung**:
- Tab: "Lớp học của tôi" / "Thời khóa biểu"
- Danh sách tất cả enrollments:
  - Mỗi enrollment card:
    - Class name, Course name
    - Status: "Đã thanh toán" / "Chưa thanh toán"
    - Schedule preview
    - Button: "Xem chi tiết" → Mở schedule detail

**API**: `GET /api/enrollment/enrollments/my-classes/?student_id={id}`

**Tổng**: **1 màn** (hoặc có thể tích hợp vào Dashboard)

---

## 📊 TỔNG KẾT

### Option 1: Tối thiểu (7 màn)
1. Dashboard
2. Placement Test (gộp 2A+2B+2C)
3. Recommended Courses
4. Course Detail + Classes
5. Enrollment Confirmation
6. Payment
7. Success + Schedule

### Option 2: Chi tiết (8-9 màn)
1. Dashboard
2. Placement Test List
3. Placement Test (Làm test)
4. Placement Test Result
5. Recommended Courses
6. Course Detail + Classes
7. Enrollment Confirmation
8. Payment
9. Success + Schedule

### Option 3: Tối ưu UX (6-7 màn với Modal/Overlay)
1. Dashboard
2. Placement Test (Modal/Fullscreen overlay)
3. Recommended Courses
4. Course Detail + Classes (2 tabs hoặc scroll)
5. Enrollment Confirmation (Modal)
6. Payment (Modal hoặc Redirect)
7. Success + Schedule (Modal hoặc Fullscreen)

---

## 🎨 ĐỀ XUẤT UI/UX

### **Recommended: Option 3 (6-7 màn với Modal)**

**Lý do**:
- Placement Test có thể là Modal/Overlay → Không cần navigate riêng
- Enrollment Confirmation có thể là Bottom Sheet/Modal
- Payment có thể là Modal hoặc Redirect external
- Giảm số lần navigate, UX mượt hơn

### **Cấu trúc màn hình đề xuất**:

```
1. Dashboard (Main Screen)
   └── Modal: Placement Test
       └── Modal: Test Result
   
2. Recommended Courses (Full Screen)
   └── Navigate to: Course Detail
   
3. Course Detail + Classes (Full Screen)
   └── Modal: Enrollment Confirmation
       └── Modal/Redirect: Payment
           └── Modal: Success + Schedule
```

---

## 📱 RESPONSIVE DESIGN

### Mobile (6-7 màn):
- Mỗi màn = 1 full screen
- Modal cho các bước nhỏ (confirmation, payment)

### Desktop/Tablet (4-5 màn):
- Có thể gộp: Course Detail + Classes = 1 màn (2 columns)
- Dashboard + My Classes = 1 màn (sidebar)

---

## ⏱️ THỜI GIAN IMPLEMENT FRONTEND

### Nếu làm từ đầu:
- **Mobile**: 3-4 ngày (6-7 màn)
- **Desktop**: 2-3 ngày (4-5 màn)
- **Tổng**: 5-7 ngày

### Nếu có design sẵn:
- **Mobile**: 2-3 ngày
- **Desktop**: 1-2 ngày
- **Tổng**: 3-5 ngày

---

## 🎯 KẾT LUẬN

**Số màn hình cần thiết**: **6-7 màn** (với Modal/Overlay)

**Breakdown**:
- **Core screens**: 4-5 màn (Dashboard, Courses, Classes, Payment, Schedule)
- **Modal/Overlay**: 2-3 màn (Placement Test, Confirmation, Success)

**Tối ưu nhất**: **6 màn** với sử dụng Modal cho các bước nhỏ


