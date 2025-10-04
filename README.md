# English Center Project

## Mục tiêu
Hệ thống quản lý trung tâm tiếng Anh, bao gồm quản lý học viên, giáo viên, lớp học, khóa học, điểm danh, tài chính, thông báo và báo cáo.

---

## Cấu trúc project

### Project
- **english_center/**: Project settings (settings, urls, wsgi, asgi)

### Apps
- **core/**: Base classes và utilities chung  
- **authentication/**: Quản lý xác thực và phân quyền (UserAccount, Role, Permission)  
- **campus/**: Quản lý cơ sở (Campus, Room, Equipment)  
- **users/**: Quản lý vai trò người dùng (Manager, Admin, Student, Teacher)  
- **courses/**: Quản lý khóa học (Course, Skill)  
- **classes/**: Quản lý lớp học (Class)  
- **enrollment/**: Quản lý đăng ký (Enrollment)  
- **sessions/**: Quản lý buổi học và điểm danh (Session, Attendance)  
- **assignments/**: Quản lý bài tập (Assignment, Submission)  
- **requests/**: Quản lý yêu cầu (ReserveRequest, LeaveRequest)  
- **notifications/**: Hệ thống thông báo *(hiện tại chưa dùng)*  
- **reporting/**: Báo cáo và thống kê *(hiện tại chưa dùng)*  
- **finance/**: Quản lý tài chính *(hiện tại chưa dùng)*  
- **test/**: Quản lý test *(sẽ tạo sau)*  

---

## Git Workflow

- **main**: nhánh ổn định (production)  
- **develop**: nhánh phát triển (integration)  
- **feature/***: nhánh code task hằng ngày  

### Quy tắc merge
- Merge `feature/*` → `develop` hằng ngày  
- Merge `develop` → `main` mỗi tuần (sau khi review & test)  

---

## Các lệnh cơ bản

### Chạy server
```bash
python manage.py runserver
