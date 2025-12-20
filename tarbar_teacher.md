TÀI LIỆU NÀY CUNG CẤP CÁC CHỨC NĂNG SẼ XUẤT HIỆN TRÊN TABBAR CỦA GIÁO VIÊN

- TRÌNH ĐỘ CỦA TÔI : chứa thông tin trình đọ của giáo viên 

- ĐĂNG KÝ LỚP HỌC : 
FLOW NHƯ SAu  : 
    - Giáo viên chọn chức năng đăng ký lớp ở tabbar -> hiện thỉ lên danh sách các lớp học chưa được gán giáo viên 
    -> giáo viên chọn lớp muốn dạy , click vào -> hệ thống sẽ check xem có bị trùng với lớp đang dạy 
    -> nếu bị trùng thì thông báo lịch bị trùng không thể đăng ký 
    -> nếu không bị trùng thì thông báo đăng ký thành công -> chuyển qua màn xem thời khóa biểu theo tuần theo lịch mới sau khi đăng ký lớp 
    ** Vấn đề của chức năng này là phải check được trùng lịch hay không  

- LỊCH DẠY CỦA TÔI : thời khóa biểu theo tuần của giáo viên 

- QUẢN LÝ BÀI TẬP : danh sách các bài tập được tạo 
    - click vào từng bài tập thì có thể xem nội dung bài tập và button danh sách bài nộp 
    - click vài button danh sách bài nộp sẽ thấy được danh sách bài nộp của học viên 
    - giáo viên có sửa bài tập nêú chưa quá deadline 
    - sau khi học viên nọp bài thì giáo viên có thể chấm điểm , nhận xét và yêu cầu nộp lại 

- LỚP Dạy CỦA TÔI : 
    - CHọn chức năng ở tabbar , hệ thống hiển thị lên danh sách lớp đang giảng dạy , click vào từng lớp 
    - khi chọn lớp thì sẽ hiên thị lên danh sách buỏio học của lớp đó ( 3 trạng thái : đã diễn ra , đang diễn ra , sắp diễn ra)
    - khi click vào buổi học thì sẽ hiênr thị thông tin buổi học đó và 2 button : tạo bài tập và điểm danh ( lớp đã diễn ra thì 2 button này bị disable , ở lớp đang diễn ra thì 2 button này được able , còn lớp sắp diễn ra thì chỉ có button tạo bài tập là able thôi )
    - Chọn button điêmr danh thì sẽ hiển thị lên danh sách học viên của lớp , giáo viên chọn trạng thái cho từng học viên và submit 
    - Chọn button tạo bài tạo thì giáo viên có thể điền các bài tập ở đây, điền các thông tin như deadline và submit 
    ( check lớp đã , đang và sắp dễn ra theo ngày nhé )

- ĐƠN XIN NGHỈ : 
    - hiển thị danh sách đơn xin nghỉ , với từng đơn , giáo viên có thể đồng ý hoặc từ chối 
    - sau khi đơn được đồng ý thì sẽ được chuyển lên cho quản lý 
    - nếu giáo viên từ chối thì đơn bị từ chối luôn 


1. TRÌNH ĐỘ CỦA TÔI
"Trình độ"  là level (Junior/Senior/Expert) và specialization (IELTS Speaking, TOEIC)
Giáo viên chỉ xem thông tin trình độ 
2. ĐĂNG KÝ LỚP HỌC
Giáo viên có thể hủy đăng ký lớp đã đăng ký , TUY NHIÊN LỚP NÀY PHẢI CHƯA CÓ HỌC VIÊN ĐĂNG KÝ 
Sau khi đăng ký thành công, có tự động chuyển màn hình SANG XEM THỜI KHÓA NIỂU GIỐNG ROLE STUDENT 
3. LỊCH DẠY CỦA TÔI
Chỉ xem theo tuần 
4. QUẢN LÝ BÀI TẬP
"Danh sách các bài tập được tạo" là  chỉ bài tập của giáo viên đó?
"Yêu cầu nộp lại" — học viên có thể nộp NHIỀU LẦN , LẦN SAU SẼ GHI ĐÈ LÊN LẦN TRƯỚC , GIÁO VIÊN CHECK THẤY CHƯA ĐƯỢC THÌ GIÁO VIÊN ĐÁNH PENDING VÀ YÊU CẦU NỘP LẠI , hOC VIÊN NỘP LẠI BAO NHIÊU LẦN CŨNG ĐƯƠCJ . NHƯNG GIÁO VIÊN VÀO CHECK MÀ ĐÁNH FAIL HOẶC PASS THÌ HỌC VIÊN KHÔNG ĐƯỢC NỘP LẠI NỮA . 
VÀ GIAO VIÊN CHỈ CHO HỌC VIÊN DUY NHẤT 1 CƠ HỘI NỘP LẠI , TỨC LÀ GIÁO VIÊN CHỈ CÓ THÊR YÊU CẦU NỘP LẠI DUY NHẤT 1 LẦN Ở 1 HỌC VIÊN Ở 1 BÀI TẬP 
5. LỚP DẠY CỦA TÔI
"Tạo bài tập" — tạo bài tập cho buổi học đó 
"Điểm danh" — các trạng thái điểm danh là  (có mặt, vắng, muộn, có phép? ( CHECK Ở CODE )
"Check lớp đã, đang và sắp diễn ra theo ngày" — TÔI KHÔNG HIỂU CÂU HỎI 
6. ĐƠN XIN NGHỈ
Đơn xin nghỉ của học viên trong các lớp giáo viên đang dạy
Sau khi giáo viên đồng ý, đơn được chuyển lên quản lý — có nghĩa là cần 2 bước duyệt (giáo viên → quản lý)? Nếu giáo viên từ chối thì đơn bị từ chối luôn, 
Giáo viên có thể xem lịch sử các đơn đã duyệt/từ chối 
