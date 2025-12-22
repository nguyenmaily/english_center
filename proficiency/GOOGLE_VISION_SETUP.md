# Hướng dẫn Setup Google Cloud Vision API (Free Tier)

## Tổng quan

Google Cloud Vision API cung cấp 1,000 requests/tháng miễn phí. Đủ cho môi trường development và testing.

## Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Click vào dropdown project ở top bar
3. Click "New Project"
4. Đặt tên: `english-center-ocr` (hoặc tên khác)
5. Click "Create"
6. Chờ vài giây để project được tạo

## Bước 2: Enable Cloud Vision API

1. Trong project vừa tạo, vào menu "APIs & Services" > "Library"
2. Tìm "Cloud Vision API"
3. Click vào và chọn "Enable"
4. Chờ vài phút để API được enable

## Bước 3: Tạo Service Account

1. Vào "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Điền thông tin:
   - **Service account name**: `english-center-ocr`
   - **Service account ID**: Tự động tạo (giữ nguyên)
   - **Description**: "Service account for OCR certificate verification"
4. Click "Create and Continue"
5. **Grant role**: Chọn một trong các role sau (theo thứ tự ưu tiên):
   - **"Cloud Vision API User"** (nếu có) - Role chuyên dụng cho Vision API
   - **"Service Usage Consumer"** ✅ **KHUYẾN KHÍCH** - Role chung cho các API services, đủ quyền để gọi Cloud Vision API
   - **"Cloud Vision API Client"** (nếu có) - Tương đương với Cloud Vision API User
   - **"Editor"** - Role rộng hơn (không khuyến khích vì quyền quá lớn)
   
   **💡 Lưu ý quan trọng**: 
   - Nếu **KHÔNG tìm thấy** "Cloud Vision API User" trong danh sách roles, hãy chọn **"Service Usage Consumer"** ✅
   - Role "Service Usage Consumer" hoàn toàn đủ để gọi Cloud Vision API và là lựa chọn phù hợp nhất
   - Role này cho phép service account sử dụng các Google Cloud APIs đã được enable trong project
6. Click "Continue" > "Done"

## Bước 4: Tạo và Download JSON Key

1. Trong danh sách Service Accounts, click vào service account vừa tạo
2. Vào tab "Keys"
3. Click "Add Key" > "Create new key"
4. Chọn "JSON"
5. Click "Create"
6. File JSON sẽ tự động download về máy
7. **Lưu file này an toàn** (không commit lên Git!)

## Bước 5: Cấu hình trong Django Project

### 5.1. Cài đặt Package

```bash
pip install google-cloud-vision
```

Thêm vào `requirements.txt`:
```
google-cloud-vision>=3.4.0
```

### 5.2. Lưu Credentials

**Option 1: Lưu trong project (không khuyến khích cho production)**
- Tạo folder `english_center/proficiency/credentials/`
- Copy file JSON vào đó: `google_vision_credentials.json`
- Thêm vào `.gitignore`:
```
proficiency/credentials/
*.json
```

**Option 2: Dùng Environment Variable (khuyến khích)**
- Lưu file JSON ở nơi an toàn (ví dụ: `C:/secure/english-center-ocr-key.json`)
- Thêm vào `.env`:
```
GOOGLE_VISION_CREDENTIALS_PATH=C:/secure/english-center-ocr-key.json
```

### 5.3. Cấu hình trong settings.py

Thêm vào `english_center/settings.py`:

```python
import os
from decouple import config

# Google Cloud Vision API
GOOGLE_VISION_CREDENTIALS_PATH = config(
    'GOOGLE_VISION_CREDENTIALS_PATH',
    default=None
)
```

## Bước 6: Test Connection

Tạo file test script `test_ocr.py`:

```python
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/credentials.json'

from google.cloud import vision

client = vision.ImageAnnotatorClient()

# Test với ảnh mẫu
with open('test_image.jpg', 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)

texts = response.text_annotations
if texts:
    print('Detected text:', texts[0].description)
else:
    print('No text detected')
```

## Pricing (Free Tier)

- **1,000 requests/tháng**: Miễn phí
- **Sau 1,000 requests**: $1.50 per 1,000 requests
- **Text Detection**: $1.50 per 1,000 requests

**Lưu ý**: Free tier đủ cho development và testing. Nếu production có nhiều requests, cần monitor và có thể cần upgrade billing account.

## Troubleshooting

### Lỗi: "Could not automatically determine credentials"
- Kiểm tra file JSON credentials có tồn tại không
- Kiểm tra path trong environment variable
- Đảm bảo file JSON có format đúng

### Lỗi: "Permission denied"
- Kiểm tra service account có một trong các role sau không:
  - "Cloud Vision API User" (nếu có)
  - **"Service Usage Consumer"** ✅ (khuyến khích dùng)
  - "Cloud Vision API Client" (nếu có)
  - "Editor" (nếu dùng role này)
- Kiểm tra API đã được enable chưa (Bước 2)
- **Nếu chưa có role nào**: Thêm role **"Service Usage Consumer"** cho service account
- Cách thêm role: Vào Service Account > "Permissions" tab > "Grant Access" > Chọn role "Service Usage Consumer"

### Lỗi: "Quota exceeded"
- Đã vượt quá 1,000 requests/tháng free tier
- Cần enable billing account để tiếp tục sử dụng

## Security Best Practices

1. **KHÔNG commit file JSON credentials lên Git**
2. Dùng environment variables hoặc secret management
3. Rotate keys định kỳ
4. Chỉ grant minimum permissions cần thiết
5. Monitor usage và costs

## Next Steps

Sau khi setup xong, xem file `ocr_utils.py` để biết cách sử dụng trong code.

