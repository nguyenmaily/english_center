# Hướng dẫn thêm dữ liệu vào Ngân hàng câu hỏi

## Tổng quan

Script `insert_question_bank_data.py` được sử dụng để thêm dữ liệu mẫu vào ngân hàng câu hỏi, bao gồm:
- **Câu hỏi đơn**: Câu hỏi độc lập với các part, skill, difficulty khác nhau
- **Nhóm câu hỏi**: Nhóm câu hỏi có context chung (đoạn văn, hội thoại)
- **Câu hỏi thuộc nhóm**: Câu hỏi liên quan đến context của nhóm

## Cách sử dụng

### 1. Thêm dữ liệu với số lượng mặc định

```bash
python manage.py insert_question_bank_data
```

- Tạo **50 câu hỏi đơn** (mặc định)
- Tạo **10 nhóm câu hỏi** (mặc định)
- Mỗi nhóm có **3-5 câu hỏi**

### 2. Tùy chỉnh số lượng

```bash
# Tạo 30 câu hỏi đơn và 5 nhóm câu hỏi
python manage.py insert_question_bank_data --count 30 --groups 5

# Tạo 100 câu hỏi đơn và 20 nhóm câu hỏi
python manage.py insert_question_bank_data --count 100 --groups 20
```

### 3. Xóa dữ liệu cũ trước khi thêm mới

```bash
python manage.py insert_question_bank_data --clear --count 50 --groups 10
```

## Cấu trúc dữ liệu được tạo

### Câu hỏi đơn (Single Questions)

- **Part**: 1, 2, 5
- **Skill**: listening, reading, speaking, writing
- **Difficulty**: easy, medium, hard
- **Audio**: Một số câu hỏi listening có audio file

### Nhóm câu hỏi (Question Groups)

- **Part**: 3, 4, 6, 7
- **Skill**: listening, reading
- **Context**: Đoạn văn hoặc hội thoại mẫu
- **Audio/Image**: 
  - Listening groups: 70% có audio file
  - Reading groups: 50% có image file

### Câu hỏi thuộc nhóm

- Mỗi nhóm có **3-5 câu hỏi**
- Câu hỏi liên quan đến context của nhóm
- Có đầy đủ 4 đáp án A, B, C, D
- Có đáp án đúng

## Ví dụ dữ liệu

### Câu hỏi Listening (Part 1, 2)

- "What is the main topic of the conversation?"
- "Where does the conversation most likely take place?"
- "What time will the meeting start?"

### Câu hỏi Reading (Part 5)

- "What is the main idea of the passage?"
- "According to the passage, what should you do first?"
- "The word 'significant' in paragraph 2 is closest in meaning to:"

### Nhóm câu hỏi Listening (Part 3, 4)

Context mẫu:
```
Man: Hi, I'm calling about the job position you advertised.
Woman: Great! Can you tell me about your experience?
Man: I've worked in sales for five years.
Woman: That sounds perfect. Can you come in for an interview tomorrow?
```

Câu hỏi:
- "What is the main purpose of the conversation?"
- "Where does this conversation most likely take place?"
- "What will the man probably do next?"

## Lưu ý

1. **Encoding**: Script sử dụng tiếng Anh trong output để tránh lỗi encoding trên Windows
2. **Dữ liệu mẫu**: Các câu hỏi được tạo tự động với nội dung mẫu, có thể chỉnh sửa sau
3. **Audio/Image files**: Các file audio và image được tạo với đường dẫn mẫu, cần upload file thật nếu muốn sử dụng
4. **Không trùng lặp**: Script không kiểm tra trùng lặp, nên sử dụng `--clear` nếu muốn reset dữ liệu

## Xem kết quả

Sau khi chạy script, bạn có thể:
1. Truy cập trang **Ngân hàng câu hỏi** trong frontend
2. Xem danh sách câu hỏi đơn và nhóm câu hỏi
3. Lọc theo part, skill, difficulty
4. Chỉnh sửa hoặc thêm câu hỏi mới

