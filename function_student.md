1. Nhóm Trình độ - "Trình độ của tôi"
Điểm đọc, nghe , nói , viết được tính từ các case sau :
- Case 1 : Học viên từng học các khóa khác trước đó ở trung tâm . điểm bài test cuối khóa sẽ được cập nhật vào đây . ( các skill không test để default = 0 ). Lưu ý , điểm của bài test cuối khóa của trung tâm chỉ có thời hạn 6 tháng kể từ ngày test 
- Case 2 : Học viên đã từng thi chứng chỉ TOEIC , (IELTS trước đó . Học viên cập nhật điểm các kĩ nang vào . nếu là toeic thì để nguyên điểm đó cập nhật . còn (IELTS thì hệ thống sẽ có logic tính toán để quy đổi sang toeic . Tổng điểm cũng tham khảo từ cách tính của toeic . (luu ý : Trung tâm này chỉ đào tào cho thi chứng chỉ toeic nen các chứng chỉ khác sẽ cần có logic để quy đổi sang toeic ) . Thời hạn của chứng chỉ là thời hanj của các điểm kĩ năng 
- Case 3 : Học viên chưa từng học ở trung tâm hay chưa có chứng chỉ thì sẽ được yêu cầu làm bài test đầu vào và kết quả của test đầu vào sẽ được cập nhật vào điểm các kĩ năng , tổng điểm , ... . Thời hạn sẽ là 6 thàng giôngs case 1. 
Điểm ở trung tâm sẽ được ưu tiên hơn điểm của chứng chỉ. Tức là nếu chứng chỉ đang còn hiệu lực nhưng học viên có bài test cuối khóa ở trung tâm thì trình đọo sẽ được cập nhật theo điểm bài test này . 
Không có case có nhiều chứng chỉ , vì chỉ cho phép học viên cập nhật không quá 1 chứng chỉ vào trình độ . Ví dụ học viên đã có 1 chứng chỉ nhưng muốn cập nhật 1 chứng chỉ mới thì chứng chỉ mới sẽ được ghi đè lên chứng chỉ cũ . 
"Ngày bắt đầu có hiệu lực" và "ngày hết hiệu lực" là cuả trình độ hiện tại , với case 2 thì nó cũng là của chứng chỉ. 

2. Nhóm Kiểm tra
2.1. "Bài kiểm tra của tôi"
Tôi có chút nhầm lẫn , không có bài test giáo viên giao ,chir có bài test đầu vào , test giữa khóa , test cuối khóa và bài test tự do . 

2.2. "Kết quả kiểm tra"
4 loại test được phân loại như thế nào?
Tôi cũng không chắc , chuts nữa check database nhé 
Tôi nghĩ nên có filter 

2.3. "Làm test" (Test tự do)
Flow làm test tự do:
Chọn loại test (đầy đủ / theo kỹ năng / theo Part)
Chọn kỹ năng/Part cụ thể
Hệ thống tạo đề ngẫu nhiên
Làm bài → Xem kết quả
"Làm theo kỹ năng" là  (Listening, Reading, Speaking, Writing?)
"Làm theo Part" (TOEIC): Part 1, 2, 3, 4, 5, 6, 7
Không giới hạn số lần làm
Có lưu lịch sử làm bài 

PHẦN TEST NÀY T SẼ CHỤP DATABASE CHO BẠN XEM , HOẶC XEM Ở APP TEST

3. Nhóm Bài tập
Câu hỏi:
"Bài tập của tôi" và "Bài đã nộp" khác nhau như thế nào?
Bài tập của tôi sẽ là danh sách các bài tập được giao , cả đã làm và chưa làm , click vào từng cái sẽ xem được nội dung đề bài giao viên giao và button bài nộp . click vào button bài nộp thì sẽ hiển thị chi tiết bài tập đã nộp lên. nếu chưa nộp thì button này bị disable 
Còn Bài đã nộp thì hiển thị danh sách bài đã nộp , tức là click vào thì sẽ xem được nội dung bạn đã nop cung điểm và đánh giá của giáo viênviên
Flow làm bài tập:
Xem danh sách bài tập ( có deadline , sau deadline thì không thể làm dc bài nữa ) 
Chọn bài( có deadline , sau deadline thì không thể làm dc bài nữa ) → Xem chi tiết
Làm bài → Nộp bài
Xem kết quả/chấm điểm
Có thể nộp lại nếu giáo viên yêu cầu)

4. Nhóm Lớp học
Câu hỏi:
"Lớp học của tôi" - 3 loại:
Đã hoàn thành: status='completed'?
Đang diễn ra: status='ongoing'?
Sắp diễn ra: status='planned' + start_date > today
"Chi tiết lớp học" hiển thị Thông tin lớp, giáo viên, lịch học, danh sách học viên và 2 button Bài tập của lớp và Điểm danh , 2 button này sẽ chuyển đến 2 trang là bài tập của lớp và trang điểm danh ( Ở ĐÂY CHỈ CÓ THÔNG TIN CỦA HỌC VIÊN ĐÓ , KHÔNG XEM ĐƯỢC CẢ LỚP - CHỈ CÓ GIÁO VIÊN MỚI XEM ĐƯỢC CẢ LỚP ) 

"Đăng ký lớp học sẽ có flow khá phức tạp như sau : 
Học viên click vào chức năng đăng ký lớp học ở tabbar 
- Bước 1 : cần có điểm đâù vào của học viên ( điểm để xác định trinhf độ hiện tại của học viên ) 
Luồng sẽ như sau : Hệ thống check trong xem học viên có điểm xác định trình độ không ? 
-> nếu có rồi thì chuyển qua bước 2 , nếu chưa có thì hiển thị thông báo : Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp và 2 button là Làm test và cập nhật chứng chỉ 
-> nếu học viên chọn button  cập nhật chứng chỉ thì chuyển qua màn cập nhật chứng chỉ -> điền loại chứng chỉ , điểm , ngày chứng chir có hiệu lực , ngày chứng chỉ hết hạn và upload ảnh chứng chỉ -> sau đó điểm được cập nhật và chuyển qua bước 2
-> nếu học viên chọn button làm test , thì chuyển qua màn test đầu vào : đề toeic 4 kĩ năng ( có thể số câu ít hơn đề thật ) và bấm thời gian . Kết quả sẽ được lưu vào điểm đầu xác định trình đọ -> sau đó điểm được cập nhật và chuyển qua bước 2
DƯỚI ĐÂY LÀ CÁC CASE ĐỂ HỌC VIÊN CÓ ĐIỂM XÁC ĐỊNH TRÌNH ĐỘ 
    + Case 1 : Khi học viên đã từng học lớp học ở trung tâm -> điểm thi cuối khóa của lớp học đó sẽ được cập nhật vào điểm xác định trình độ ( Điều kiện là thời hạn trong 6 thangs : tức là tính từ lúc có điểm đó đến hiện tại <=6 tháng  ) . Nếu thời hạn quá 6 tháng thì học viên phải chuyển qua case 3 
    + Case 2 : Học viên đã có chứng chỉ : HỌC Viên dã cập nhật các thông tin điền loại chứng chỉ , điểm , ngày chứng chir có hiệu lực , ngày chứng chỉ hết hạn và upload ảnh chứng chỉ 
    + Case 3 : Học viên chưa từng học ở trung tâm hay chưa có chứng chỉ thì sẽ được yêu cầu làm bài test đầu vào và kết quả của test đầu vào sẽ được cập nhật vào điểm các kĩ năng , tổng điểm , ... . Thời hạn sẽ là 6 thàng giôngs case 1. 
- Bước 2 : Hiển thị đầy đủ danh sách khóa học , nhưng chỉ có khóa học đủ điều kiện đầu vào thì học viên mới có thể chọn , còn khác khóa học khác thì disable và học viên chọn vào thì thông báo không đủ điều kiện 
- Bước 3 : sau khi chọn được khóa học , hêj thống hiện thị đầy đủ danh sách lớp học của lớp đó đã có id_teacher ( tức là giáo viên đã đăng ký rồi) và quản lý đã approve rồi , lớp này còn phải chưa đủ học viên và trạng thái phải là sắp diễn ra . Học viên sẽ học lớp 
- Bước 4 : khi chọn lớp xong thì hệ thống sẽ hiển thị thông tin về lớp này ( lấy ở bảng class nhé ) và button thanh toán 
- Bước 5 Thanh toán : Học viên sẽ được chọn 2 hình thức là tiền mặt ( nộp trực tiêp ở trung tâp hoặc chuyển khoản (chuyển vào vnpay , ... ) . Thời hạn là 2 ngày . Trong 2 ngày này nếu chưa thanh toán thì đăng ký sẽ pending lại , còn nếu sau 2 ngày thì đang ký này sẽ bị cancel . Còn 1 TH là nếu trong lúc chừo thanh toán mà lớp đã đủ slot rồi thì đăng ký này cũng bị cancel ( có thông báo nhé ) . 
- Bước 6 : sau khi thanh toán xong thì sẽ được thông báo đăng ký lớp thành công và chuyển qua giao diện xem thời khóa biểu ( LUU Ý : THỜI ĐIỂM TẠO ĐĂNG KÝ KHÔNG QUAN TRỌNG BẰNG THỜI ĐIỂM ĐĂNG KSY HOÀN THÀNH ) 


"Lịch học" theo tuần:
Chọn tuần từ calendar/date picker
Hiển thị tất cả lớp DIỄN RA trong thời gian chọn , TUY NHIÊN CÓ ROLE LÀ HỌC VIÊN CHỈ ĐƯỢC HỌC 1 LỚP TRONG 1 KHOẢNG THỜI GIAN. TỨC LÀ KHÔNG BAO GIỪO CÓ CHUYỆN HỌC 2 HAY NHIỀU LỚP HỌC TRONG 1 KHOẢNG THỜI GIAN 

"Khóa học" - danh sách khóa học:
hiển thị đầy đủ các khóa học , học viên có thể xem đầy đủ thông tin của khóa học . NHUNG CHỈ KHI TRÌNH ĐỘ CỦA HỌC VIÊN THÕA MÃN ĐIỀU KIỆN ĐẦU VÀO CỦA KHÓA HỌC THÌ button Đăng ký với ABLE , còn lại thì DISABLE 

5. Nhóm Yêu cầu
5.1. "Đơn xin nghỉ"
Câu hỏi:
Flow tạo đơn:
Chọn lớp
Chọn buổi học (session) hoặc ngày?
Điền lý do?
Gửi → Chờ giáo viên , SAU KHI giao viên duyệt thì chuyển qua cho mânager. Đơn này chỉ có hiểu lực khi đủ cả 2 aprrove. 
Có thể xin nghỉ nhiều buổi cùng lúc , tuy nhiên tổng số buổi nghỉ quá 10% tổng bubuc thì học viên sẽ không được cam kết nữa . 
Có thể hủy đơn đã gửi nếu đơn đó chưa được giáo viên xem ( duyẹt hoặc từ chối ) 
Xem lịch sử đơn xin nghỉ

5.2. "Yêu cầu bảo lưu"
Câu hỏi:
Flow tạo yêu cầu:
Chọn lớp
Chọn thời gian bảo lưu (start_date, end_date)?
Điền lý do?
Gửi → Chờ duyệt?
Bảo lưu có nghĩa là tạm dừng lớp học hiện tại va được thay thế bằng 1 lớp học khác ( cùng 1 khóa học )
TUY NHIÊN : BẢO LƯU SẼ CÓ CÁC YÊU CẦU LÀ : BẠN CHƯA HỌC QUÁ 20% LỚP HIỆN TẠI VÀ LÝ DO CHÍNH ĐÁNG -> ĐƠN BẢO LƯU NÀY DO QUẢN LÝ DUYỆT ) VÀ ĐƠN BẢO LƯU NÀY SẼ CÓ THỜI HẠN TRONG VÒNG 3 THÁNG 


CÁC ĐIỂM CẦN LÀM RÕ THÊM
Phân quyền: Học viên không thể xem điểm của học viên khác 
Thông báo: Có hệ thống thông báo cho các sự kiện (test mới, bài tập mới, đơn được duyệt)
Upload file: Bài tập và chứng chỉ có upload file 
Điểm danh: Học viên có thể xem lịch sử điểm danh của mình 
.



TÓM TẮT CÁC CÂU HỎI QUAN TRỌNG
Trình độ: 
Lưu điểm 4 kỹ năng ở BẢNG StudentCertificate đi , Hãy cho tôi biết bảng này có các thuộc tính bào nhé 
Công thức quy đổi IELTS → TOEIC? TÔI KHÔNG BIẾT , BẠN HÃY THAM KHẢO CÁC TÀI LIỆU NHÉ 

Test: 
- Phân loại 4 loại test trong database như thế nào? dựa theo exam_type , CÓ CẬP NHẬT DATABASE THÌ NÓI T BIẾT NHÉ 
- Test giữa/cuối khóa gắn với lớp CHỨ 

Đăng ký: 
- Logic ưu tiên điểm xác định trình độ? 
Bước 1 - "Điểm xác định trình độ":
Case 1: Test cuối khóa - Lấy từ StudentProgress.final_score
Case 2: Chứng chỉ - Lấy từ StudentCertificate đã verified
Case 3: Test đầu vào - Lấy từ StudentProgress.placement_score
Logic ưu tiên: Test cuối khóa > Chứng chỉ > Test đầu vào
Ai cập nhật thanh toán tiền mặt? -> QUẢN LÝ 
Deadline 2 ngày: Từ lúc tạo enrollment 
Bước 6: "Thời điểm đăng ký hoàn thành" = thời điểm thanh toán thành công

Nhóm Yêu cầu
Câu hỏi:
Đơn xin nghỉ:
"Tổng số buổi nghỉ quá 10% tổng buổi": khi đăng kí lớp học sẽ biết lớp đó có tổng bao nhiêu buỏi phải không , ví dụ nếu có 24 buổi thì chỉ được nghỉ 2 buổi thôi 
"Không được cam kết nữa": commitment_status = 'canceled'
Có thể xin nghỉ nhiều buổi cùng lúc: với nhiều đơn , 1 đơn chỉ gán với 1 buổi thôi 

Bảo lưu:
"Chưa học quá 20% lớp hiện tại":  (số session đã học / tổng session)
"Thay thế bằng 1 lớp học khác (cùng 1 khóa học)": Học viên tự chọn lớp mới , tuy nhiên hoc sẽ nhân được thông báo  nhắc đăng ký lớp  nếu là sắp hết hạn bảo lưu trước 10 ngày 
"Thời hạn trong vòng 3 tháng": Từ khi được duyệt



StudentCertificate - Điểm 4 kỹ năng: Model hiện chỉ có score (tổng điểm).  thêm reading_score, listening_score, speaking_score, writing_score và trường loại chứng chỉ và trường url ảnh chứng chỉ vào bảng student_certificates 
Công thức quy đổi IELTS → TOEIC: Cần công thức cụ thể. Bạn  tìm tài liệu tham khảo và implement
Exam_type cho test tự do: Hiện có placement, midterm, final. Có  thêm practice cho test tự do 
Test giữa/cuối khóa gắn với lớp: ExamInstance có liên kết với Class không, hay chỉ qua ExamBlueprint.exam_type? => hiện tại bảng ExamInstance  không có liên kết với Class  , nói thật tôi chẳng hiểu các bảng liên quan đến exam 