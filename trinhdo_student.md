Chào bạn, đây là bản tài liệu chi tiết (Technical Design Document) cho chức năng **"Hồ sơ năng lực tiếng Anh của tôi"** dựa trên tất cả các logic tối ưu mà chúng ta đã thống nhất.

---

# TÀI LIỆU CHI TIẾT CHỨC NĂNG: HỒ SƠ NĂNG LỰC TIẾNG ANH

## 1. TỔNG QUAN CHỨC NĂNG

Chức năng này là nơi lưu trữ, quản lý và xác thực toàn bộ quá trình phát triển năng lực tiếng Anh của học viên. Hệ thống sử dụng dữ liệu này để đưa ra các gợi ý khóa học chính xác theo trình độ thực tế.

---

## 2. CẤU TRÚC DỮ LIỆU (DATABASE)

### Bảng chính: `student_certificates`

Bảng này lưu lại tất cả các sự kiện thay đổi điểm số năng lực.

| Trường dữ liệu | Kiểu dữ liệu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | BigInt | Primary Key |  |
| `student_id` | Int | Foreign Key | Liên kết bảng `users`. |
| `skill_group` | Enum | 'LR', 'SW' | **LR**: Listening-Reading; **SW**: Speaking-Writing. |
| `source_type` | Enum | 'CERT', 'ENTRY', 'FINAL' | **CERT**: Chứng chỉ; **ENTRY**: Test đầu vào; **FINAL**: Test cuối khóa. |
| `score_1` | Int |  | Listening hoặc Speaking. |
| `score_2` | Int |  | Reading hoặc Writing. |
| `total_score` | Int | Not Null | Điểm tổng dùng để xét lớp. |
| `test_date` | Date | Not Null | Ngày thi hoặc ngày làm bài. |
| `expired_date` | Date | Not Null | Ngày hết hạn của kết quả. |
| `proof_image` | String | Nullable | Link ảnh chứng chỉ. |
| `status` | Enum | Default 'PENDING' | 'VERIFIED' (Đã xác thực), 'PENDING' (Chờ duyệt), 'REJECTED' (Từ chối). |
| `admin_id` | Int | Foreign Key (Null) | ID Admin thực hiện duyệt (null nếu hệ thống tự duyệt). |
| verification_method	Enum		'AUTO_OCR' hoặc 'MANUAL_ADMIN'.

---

## 3. LUỒNG LOGIC CHÍNH (MAIN FLOW)

### 3.1. Logic Xác định Năng lực Hiện tại (Highlight Card)

Hệ thống xác định "Năng lực hiện tại" để hiển thị to nhất và dùng để gợi ý khóa học bằng cách truy vấn:

1. Lọc theo `student_id` và `skill_group`.
2. Phải có `status = 'VERIFIED'`.
3. Phải còn hạn: `expired_date >= Current_Date`.
4. Sắp xếp theo `test_date` mới nhất.

### 3.2. Logic Gợi ý Khóa học

Hệ thống Mapping `total_score` của bản ghi "Năng lực hiện tại" với dải điểm `min_score` - `max_score` trong bảng `courses`.

* **Lưu ý:** Gợi ý khóa học L&R dựa trên điểm LR; khóa học S&W dựa trên điểm SW.

---

## 4. CÁC CHỨC NĂNG CON (SUB-FUNCTIONS)

### 4.1. Chức năng: Cập nhật chứng chỉ 

Dành cho học viên đã có bằng TOEIC chính thức từ IIG.
Đây là chức năng trọng tâm sử dụng phần mềm bên thứ ba Google Cloud Vision API để tự động hóa quy trình phê duyệt.

* **Luồng xử lý:**
1. Học viên chọn `skill_group` (LR hoặc SW).
2. Nhập điểm thành phần, điểm tổng và **Ngày thi**.
3. Upload ảnh minh chứng.
4. Hệ thống tự tính `expired_date = test_date + 2 năm`.
5. Gọi API OCR: Hệ thống gửi ảnh đến Google Cloud Vision API để trích xuất dữ liệu văn bản (text extraction).
So khớp tự động (Matching Logic): Hệ thống so sánh dữ liệu học viên vừa nhập với dữ liệu máy quét được:
Case A (Khớp > 90%): Thông tin trùng khớp hoàn toàn hoặc sai số không đáng kể.
Hành động: Chuyển status thành 'VERIFIED' ngay lập tức.
Case B (Không khớp hoặc Không đọc được): Ảnh mờ, thông tin học viên nhập khác với ảnh, hoặc API không nhận diện được định dạng.
Hành động: Chuyển status thành 'PENDING'.
Thông báo: "Thông tin chưa khớp với ảnh, hệ thống đã gửi yêu cầu phê duyệt cho Admin. Bạn vẫn có thể tìm hiểu kĩ hơn về các khóa học ."



### 4.2. Chức năng: Kiểm tra đầu vào (Placement Test)

Dành cho học viên chưa có bằng hoặc bằng đã hết hạn.

* **Luồng xử lý:**
1. **Kiểm tra điều kiện (Validation):**
* Nếu `skill_group` tương ứng vẫn còn bản ghi `VERIFIED` và còn hạn -> **Disable** nút/option test nhóm đó.
* Nếu đã hết hạn hoặc chưa có dữ liệu -> **Enable**.


2. **Chọn nhóm kỹ năng:** Học viên chọn LR hoặc SW (nếu cả 2 đều hết hạn).
3. **Làm bài & Chấm điểm:** Hệ thống tự chấm sau khi nộp bài.
4. **Lưu kết quả:**
* `source_type = 'ENTRY_TEST'`.
* `status = 'VERIFIED'` (Hệ thống tự duyệt).
* `expired_date = today + 6 tháng`.





### 4.3. Chức năng: Cập nhật điểm cuối khóa (Automatic Update)

Xảy ra khi học viên hoàn thành một khóa học tại trung tâm.

* **Luồng xử lý:**
1. Giáo viên/Hệ thống nhập điểm thi cuối khóa.
2. Hệ thống tự động đẩy dữ liệu vào bảng `proficiency_logs`.
3. `source_type = 'FINAL_TEST'`.
4. `status = 'VERIFIED'`.
5. `expired_date = today + 6 tháng`.



---

## 5. GIAO DIỆN NGƯỜI DÙNG (UI SPECIFICATION)

### A. Khu vực Highlight (Top)

* Hiển thị 2 Card lớn: **Current L&R** và **Current S&W**.
* Nếu chưa có dữ liệu/hết hạn: Hiển thị trạng thái "Chưa xác định" hoặc "Hết hạn".

### B. Khu vực Action Buttons

* **Nút "Cập nhật chứng chỉ":** Luôn hiển thị.
* **Nút "Kiểm tra đầu vào":**
* Chỉ sáng khi 1 trong 2 hoặc cả 2 nhóm kỹ năng bị "Outdate".
* Khi click, popup chọn nhóm kỹ năng chỉ sáng các lựa chọn đã hết hạn.



### C. Khu vực Timeline (History)

* Danh sách các thẻ nhỏ xếp theo thời gian mới nhất.
* **Filter:** Có bộ lọc theo `LR` hoặc `SW` để học viên dễ theo dõi tiến trình của từng nhóm kỹ năng riêng biệt.

---

## 6. CÁC CÂU HỎI CẦN LÀM RÕ (QUESTIONS & CLARIFICATIONS)

Sau khi đọc kỹ tài liệu và tìm hiểu codebase, tôi có một số câu hỏi cần làm rõ:

### 6.1. Về Cấu trúc Database

**Q1:** Dòng 22 - `student_id` là `Int` và Foreign Key đến bảng `users`, nhưng trong codebase hiện tại, model `Student` sử dụng `UUIDField` làm primary key. Vậy `student_id` trong bảng `student_certificates` nên là:
- `Int` (ID từ bảng `user_accounts`)?
- Hay `UUID` (ID từ bảng `students`)?
=> Answer : student_id là uuid và lấy từ id của bảng students 

**Q2:** Dòng 33 - Trường `verification_method` thiếu format trong bảng. Cần bổ sung:
- Kiểu dữ liệu: Enum
- Giá trị mặc định (nếu có)
- Có thể null không?
=> Answer : kiểu dữ liểu của trường verification_method là enum với các giá trị auto_ocr và manual_admin , giá trị mặc định là là auto_ocr . trường nay này không null nhé 

**Q3:** Dòng 105 - Tài liệu đề cập đến bảng `proficiency_logs` nhưng bảng chính là `student_certificates`. Có phải:
- `proficiency_logs` là tên cũ và đã đổi thành `student_certificates`?
- Hay đây là 2 bảng khác nhau? Nếu vậy, cần mô tả rõ mối quan hệ.
=> Answer : `proficiency_logs` là tên cũ và đã đổi thành `student_certificates`

### 6.2. Về Logic Xử lý

**Q4:** Dòng 91 - `source_type = 'ENTRY_TEST'` nhưng trong enum ở dòng 24 chỉ có `'ENTRY'`. Cần thống nhất:
- Dùng `'ENTRY'` hay `'ENTRY_TEST'`?
- Tương tự, `'FINAL'` hay `'FINAL_TEST'`?
=> Answer : tôi thống nhất lại là source_type có dạng enum với các giá trị : certificate , enty_test , final_testtest

**Q5:** Dòng 70 - Logic so khớp OCR với ngưỡng "Khớp > 90%":
- Công thức tính % khớp cụ thể như thế nào? (So sánh từng trường nào: điểm số, ngày thi, tên học viên?)
- Có cần so khớp tên học viên trên chứng chỉ với tên trong hệ thống không?
- Nếu điểm số có sai số nhỏ (ví dụ: nhập 850 nhưng OCR đọc 845), có được coi là khớp không?
=> Answer : So sánh từng trường nào: điểm số, ngày thi, tên học viên , tên học viên trên chứng chỉ với tên trong hệ thống ( lấy tên từ trường full_name trong user_accounts ). Nếu điêmr có sai số nhỏ như vd thì là khớp 

**Q6:** Dòng 68 - `expired_date = test_date + 2 năm`:
- Có cần xử lý trường hợp năm nhuận không?
- Nếu `test_date` là ngày trong quá khứ (ví dụ: thi cách đây 1 năm), `expired_date` vẫn tính từ `test_date` hay từ ngày hiện tại?
=> Answer : vd dụ test_date = 12/3/2025 thì expired_date = 12/3/2027 . Không cần check năm nhuần hay không . test_date là ngày thi và expired_date luôn ting theo test_date 

**Q7:** Dòng 93 và 108 - `expired_date = today + 6 tháng`:
- "6 tháng" là chính xác 180 ngày hay tính theo tháng (ví dụ: 1/1/2024 -> 1/7/2024)?
- Có cần xử lý trường hợp tháng có số ngày khác nhau không?
=> Answer : `expired_date = today + 6 tháng`: thif 1/1/2024 -> 1/7/2024 ( không cần check ngày của tháng ) 

### 6.3. Về Chức năng Placement Test

**Q8:** Dòng 89 - "Hệ thống tự chấm sau khi nộp bài":
- Placement Test này có liên quan đến module `tests` hiện có trong codebase không?
- Hay đây là một bài test riêng biệt chỉ dành cho chức năng này?
- Cấu trúc câu hỏi và cách tính điểm như thế nào?
=> Answer : có nhé , có trong codebase tests nhé 

**Q9:** Dòng 88 - Học viên có thể làm Placement Test cho cả 2 nhóm kỹ năng (LR và SW) cùng lúc không?
- Hay phải làm từng cái một?
- Nếu làm cả 2, có cần làm tuần tự hay song song?
=> Answer : Không Test cho cả 2 nhóm kỹ năng (LR và SW) cùng lúc , nhóm kĩ năng năng LR có 1 bài test và nhóm kĩ năng SW có 1 bài test . Nếu học viên muốn test cả 2 nhóm kĩ năng thì kàm tuần tự 2 bài thi 

### 6.4. Về Google Cloud Vision API

**Q10:** Dòng 68 - Tích hợp Google Cloud Vision API:
- Đã có credentials và setup Google Cloud Vision API chưa?
- Cần tạo service account và lưu credentials ở đâu trong project?
- Có cần xử lý rate limiting hoặc quota của API không?
- Chi phí API có cần theo dõi không?
=> Answer : Chưa có gì cả , Hãy hướng dâ dẫn tôi từng bước nhé , tôi định chỉ làm ở mức free thoi 

**Q11:** Dòng 69 - Logic so khớp:
- OCR sẽ trích xuất những thông tin gì từ ảnh chứng chỉ? (Điểm số, ngày thi, tên, số chứng chỉ?)
- Format của chứng chỉ TOEIC có chuẩn không? (IIG có nhiều format khác nhau không?)
- Có cần xử lý trường hợp ảnh bị xoay, cắt, hoặc chất lượng kém không?
=> Answer : Các trường cần cần lấy : tổng điểm( total_score ) , loại chứng chỉ (LISTEN AND READING hay SPEAKING AND WRITING ) , name , test_date ). IIG Có 1 loại chứng chỉ thôi ( 1 format ) . KHông xử lý các TH ảnh bị xoay, cắt, hoặc chất lượng kém , những TH này để pending cchuyển qua admin 

### 6.5. Về UI/UX

**Q12:** Dòng 119 - Trạng thái "Chưa xác định" hoặc "Hết hạn":
- Card hiển thị gì khi "Chưa xác định"? (Có nút CTA không?)
- Card hiển thị gì khi "Hết hạn"? (Có hiển thị điểm cũ và ngày hết hạn không?)
=> Answer :

**Q13:** Dòng 133 - Timeline History:
- Có hiển thị cả các bản ghi `PENDING` và `REJECTED` không?
- Học viên có thể xem chi tiết từng bản ghi (click vào card) không?
- Có thể xem lại ảnh chứng chỉ đã upload không?
=> Answer :chỉ hiển thị bạn ghi dc verifi thôi 

### 6.6. Về Gợi ý Khóa học

**Q14:** Dòng 50-52 - Logic gợi ý khóa học:
- Bảng `courses` có trường `min_score` và `max_score` chưa?
- Nếu một học viên có điểm nằm giữa 2 khóa học, gợi ý khóa nào? (Khóa thấp hơn hay cao hơn?)
- Có cần xét đến các yếu tố khác không? (Ví dụ: khóa học đã đăng ký, lịch học, v.v.)
=> Answer : Không cần gọi ý khóa học đâu , để chức năng khác làm 

### 6.7. Về Cập nhật Điểm Cuối khóa

**Q15:** Dòng 104 - "Giáo viên/Hệ thống nhập điểm thi cuối khóa":
- Điểm này được nhập ở đâu? (Trong module nào của hệ thống?)
- Có liên quan đến model `StudentProgress` hiện có không?
- Khi nào thì trigger việc cập nhật này? (Sau khi hoàn thành khóa học? Sau khi thi cuối khóa?)
=> Answer : điêm thi này sẽ là bài test của cuối khóa , ngay khi có kêt quả bài test thì nó được update qua đây luôn . Nó có liên quan đến  model `StudentProgress` 

**Q16:** Dòng 105 - "Hệ thống tự động đẩy dữ liệu":
- Có cần validation điểm số không? (Ví dụ: điểm phải trong khoảng hợp lệ) 
- Nếu học viên có nhiều khóa học, mỗi khóa học sẽ tạo 1 bản ghi riêng trong `student_certificates`?
=> Answer : điểm nhóm kĩ năng LR là 0 -> 990 , điểm nhóm kĩ năng SW là 0 - 400 , học viên có nhiều khóa học, mỗi khóa học sẽ tạo 1 bản ghi riêng trong `student_certificates`

---

**Bước tiếp theo:** Sau khi làm rõ các câu hỏi trên, tôi sẽ:
1.Xác định role và permission đấy nhé ( chức năng này chỉ có student có thôi ) 
2. Viết câu sql cho tôi tạo bảng ở dưới database 
1. Tạo model `StudentCertificate` trong Django
2. Viết các API endpoints cho chức năng này
3. Tích hợp Google Cloud Vision API cho OCR
4. Thiết kế UI/UX theo specification