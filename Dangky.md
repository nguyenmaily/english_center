TÀI LIỆU NAY LIÊN QUAN ĐẾN CHỨC NĂNG ĐĂNG KÝ LỚP HỌC CỦA HỌC VIÊN , VÀ ĐĂNG KÝ LỚP DẠY CỦA GIẢNG VIÊN 

1. CHỨC NĂNG ĐĂNG KÝ LỚP DẠY CỦA GIẢNG VIÊN 
- Giáo viên chọn chức năng đăng ký lớp ở tabbar -> hiện thỉ lên danh sách các lớp học chưa được gán giáo viên 
-> giáo viên chọn lớp muốn dạy , click vào -> hệ thống sẽ check xem có bị trùng với lớp đang dạy 
-> nếu bị trùng thì thông báo lịch bị trùng không thể đăng ký 
-> nếu không bị trùng thì thông báo đăng ký thành công -> chuyển qua màn xem thời khóa biểu theo tuần theo lịch mới sau khi đăng ký lớp 
** Vấn đề của chức năng này là phải check được trùng lịch hay không  

2. CHỨC NĂNG ĐĂNG KÝ LỚP HỌC CỦA HỌC VIÊN 
Học viên click vào chức năng đăng ký lớp học ở tabbar 
- Bước 1 : cần có điểm đâù vào của học viên ( điểm để xác định trinhf độ hiện tại của học viên ) 
Luồng sẽ như sau : Hệ thống check trong xem học viên có điểm xác định trình độ không ? 
-> nếu có rồi thì chuyển qua bước 2 , nếu chưa có thì hiển thị thông báo : Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp và 2 button là Làm test và cập nhật chứng chỉ 
-> nếu học viên chọn button  cập nhật chứng chỉ thì chuyển qua màn cập nhật chứng chỉ -> điền loại chứng chỉ , điểm , ngày chứng chir có hiệu lực , ngày chứng chỉ hết hạn và upload ảnh chứng chỉ -> sau đó điểm được cập nhật và chuyển qua bước 2
-> nếu học viên chọn button làm test , thì chuyển qua màn test đầu vào : đề toeic 4 kĩ năng ( có thể số câu ít hơn đề thật ) và bấm thời gian . Kết quả sẽ được lưu vào điểm đầu xác định trình đọ -> sau đó điểm được cập nhật và chuyển qua bước 2
DƯỚI ĐÂY LÀ CÁC CASE ĐỂ HỌC VIÊN CÓ ĐIỂM XÁC ĐỊNH TRÌNH ĐỘ 
    + Case 1 : Khi học viên đã từng học lớp học ở trung tâm -> điểm thi cuối khóa của lớp học đó sẽ được cập nhật vào điểm xác định trình độ ( Điều kiện là thời hạn trong 6 thangs : tức là tính từ lúc có điểm đó đến hiện tại <=6 tháng  ) . Nếu thời hạn quá 6 tháng thì học viên phải chuyển qua case 3 
    + Case 2 : Học viên đã có chứng chỉ : HỌC Viên dã cập nhật các thông tin điền loại chứng chỉ , điểm , ngày chứng chir có hiệu lực , ngày chứng chỉ hết hạn và upload ảnh chứng chỉ 
    + Case 3 : 
