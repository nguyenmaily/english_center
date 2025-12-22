"""
Utility functions cho Google Cloud Vision API OCR
"""
import os
import re
from typing import Dict, Optional, Tuple
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Lazy import để tránh lỗi khi module chưa được cài đặt
try:
    from google.cloud import vision
    VISION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google Cloud Vision not available: {e}")
    vision = None
    VISION_AVAILABLE = False


def get_vision_client():
    """
    Tạo và trả về Google Cloud Vision client
    
    Returns:
        vision.ImageAnnotatorClient: Vision API client hoặc None nếu không khả dụng
    """
    if not VISION_AVAILABLE:
        logger.warning("Google Cloud Vision library not installed. Please install: pip install google-cloud-vision")
        return None
    
    credentials_path = getattr(settings, 'GOOGLE_VISION_CREDENTIALS_PATH', None)
    
    if credentials_path and os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    elif not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        logger.warning("Google Vision credentials not configured. OCR will not work.")
        return None
    
    try:
        client = vision.ImageAnnotatorClient()
        return client
    except Exception as e:
        logger.error(f"Error creating Vision client: {e}")
        return None


def extract_text_from_image(image_url: str) -> Optional[str]:
    """
    Trích xuất text từ ảnh bằng Google Cloud Vision API
    
    Args:
        image_url: URL của ảnh (hoặc path local)
    
    Returns:
        str: Text được trích xuất, None nếu lỗi
    """
    client = get_vision_client()
    if not client:
        return None
    
    try:
        # Nếu là URL, dùng image.source
        # Nếu là path local, dùng image.content
        image = vision.Image()
        
        if image_url.startswith('http://') or image_url.startswith('https://'):
            image.source.image_uri = image_url
        else:
            # Local file path
            with open(image_url, 'rb') as image_file:
                image.content = image_file.read()
        
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            # Trả về toàn bộ text (texts[0] chứa tất cả text)
            return texts[0].description
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None


def parse_toeic_certificate(text: str) -> Dict[str, Optional[str]]:
    """
    Parse text từ OCR để lấy thông tin chứng chỉ TOEIC
    
    Args:
        text: Text được trích xuất từ OCR
    
    Returns:
        dict: {
            'total_score': str hoặc None,
            'skill_group': 'LR' hoặc 'SW' hoặc None,
            'name': str hoặc None,
            'test_date': str hoặc None (format: YYYY-MM-DD)
        }
    """
    if not text:
        return {
            'total_score': None,
            'skill_group': None,
            'name': None,
            'test_date': None,
        }
    
    result = {
        'total_score': None,
        'skill_group': None,
        'name': None,
        'test_date': None,
    }
    
    # Tìm total_score (số điểm tổng, thường là số lớn nhất)
    # Pattern: số có 3-4 chữ số (TOEIC: 0-990 cho LR, 0-400 cho SW)
    score_patterns = [
        r'\b(\d{3,4})\b',  # Số 3-4 chữ số
        r'SCORE[:\s]*(\d{3,4})',
        r'TOTAL[:\s]*(\d{3,4})',
        r'(\d{3,4})\s*POINTS?',
    ]
    
    for pattern in score_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Lấy số lớn nhất (thường là total_score)
            scores = [int(m) for m in matches if m.isdigit()]
            if scores:
                max_score = max(scores)
                if 0 <= max_score <= 990:  # Valid TOEIC score range
                    result['total_score'] = str(max_score)
                    break
    
    # Tìm skill_group (LISTENING AND READING hoặc SPEAKING AND WRITING)
    text_upper = text.upper()
    if 'LISTENING' in text_upper and 'READING' in text_upper:
        result['skill_group'] = 'LR'
    elif 'SPEAKING' in text_upper and 'WRITING' in text_upper:
        result['skill_group'] = 'SW'
    elif 'L&R' in text_upper or 'L AND R' in text_upper:
        result['skill_group'] = 'LR'
    elif 'S&W' in text_upper or 'S AND W' in text_upper:
        result['skill_group'] = 'SW'
    
    # Tìm name (thường nằm sau "NAME" hoặc "CANDIDATE NAME")
    name_patterns = [
        r'(?:NAME|CANDIDATE\s+NAME)[:\s]+([A-Z\s]+)',
        r'NAME[:\s]+([A-Z][A-Z\s]{5,30})',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Loại bỏ các ký tự không hợp lệ
            name = re.sub(r'[^A-Z\s]', '', name, flags=re.IGNORECASE).strip()
            if len(name) > 3:  # Tên phải có ít nhất 3 ký tự
                result['name'] = name
                break
    
    # Tìm test_date (format: DD/MM/YYYY hoặc MM/DD/YYYY hoặc YYYY-MM-DD)
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY hoặc MM/DD/YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
        r'(?:DATE|TEST\s+DATE)[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Lấy match đầu tiên
            match = matches[0]
            if len(match) == 3:
                # Cố gắng parse thành YYYY-MM-DD
                try:
                    if len(match[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = match
                    else:  # DD/MM/YYYY hoặc MM/DD/YYYY
                        # Giả sử format DD/MM/YYYY (có thể cần điều chỉnh)
                        day, month, year = match
                    
                    # Validate
                    if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                        result['test_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        break
                except (ValueError, IndexError):
                    continue
    
    return result


def calculate_match_percentage(
    user_data: Dict,
    ocr_data: Dict,
    user_name: str
) -> float:
    """
    Tính % khớp giữa dữ liệu user nhập và OCR
    
    Args:
        user_data: {
            'total_score': int,
            'skill_group': 'LR' hoặc 'SW',
            'test_date': date object,
            'name': str (từ user_accounts.fullname)
        }
        ocr_data: {
            'total_score': str hoặc None,
            'skill_group': 'LR' hoặc 'SW' hoặc None,
            'test_date': str hoặc None (YYYY-MM-DD),
            'name': str hoặc None
        }
        user_name: Tên học viên từ user_accounts.fullname
    
    Returns:
        float: % khớp (0-100)
    """
    total_fields = 4
    matched_fields = 0
    
    # 1. So khớp total_score (cho phép sai số ±5)
    if ocr_data.get('total_score'):
        try:
            ocr_score = int(ocr_data['total_score'])
            user_score = user_data.get('total_score', 0)
            if abs(ocr_score - user_score) <= 5:
                matched_fields += 1
        except (ValueError, TypeError):
            pass
    
    # 2. So khớp skill_group
    if ocr_data.get('skill_group') == user_data.get('skill_group'):
        matched_fields += 1
    
    # 3. So khớp test_date (cho phép sai số ±1 ngày)
    if ocr_data.get('test_date') and user_data.get('test_date'):
        try:
            from datetime import datetime
            ocr_date = datetime.strptime(ocr_data['test_date'], '%Y-%m-%d').date()
            user_date = user_data['test_date']
            if isinstance(user_date, str):
                user_date = datetime.strptime(user_date, '%Y-%m-%d').date()
            
            # So sánh với sai số ±1 ngày
            from datetime import timedelta
            if abs((ocr_date - user_date).days) <= 1:
                matched_fields += 1
        except (ValueError, TypeError):
            pass
    
    # 4. So khớp name (fuzzy matching)
    if ocr_data.get('name') and user_name:
        ocr_name = ocr_data['name'].upper().strip()
        user_name_upper = user_name.upper().strip()
        
        # Loại bỏ khoảng trắng thừa
        ocr_name = ' '.join(ocr_name.split())
        user_name_upper = ' '.join(user_name_upper.split())
        
        # So sánh (có thể cải thiện bằng fuzzy matching library)
        if ocr_name == user_name_upper:
            matched_fields += 1
        elif ocr_name in user_name_upper or user_name_upper in ocr_name:
            # Partial match - cho 0.5 điểm
            matched_fields += 0.5
    
    # Tính %
    match_percentage = (matched_fields / total_fields) * 100
    return match_percentage


def verify_certificate_with_ocr(
    image_url: str,
    user_data: Dict,
    user_name: str
) -> Tuple[bool, str, Dict]:
    """
    Verify chứng chỉ bằng OCR
    
    Args:
        image_url: URL hoặc path của ảnh chứng chỉ
        user_data: Dữ liệu user nhập
        user_name: Tên học viên
    
    Returns:
        tuple: (is_verified: bool, message: str, ocr_data: dict)
    """
    # Trích xuất text từ ảnh
    text = extract_text_from_image(image_url)
    if not text:
        return False, "Không thể đọc được text từ ảnh. Vui lòng kiểm tra lại chất lượng ảnh.", {}
    
    # Parse thông tin từ text
    ocr_data = parse_toeic_certificate(text)
    
    # Tính % khớp
    match_percentage = calculate_match_percentage(user_data, ocr_data, user_name)
    
    # Quyết định
    if match_percentage >= 90:
        return True, f"Thông tin khớp {match_percentage:.1f}%. Chứng chỉ đã được xác thực tự động.", ocr_data
    else:
        return False, f"Thông tin khớp {match_percentage:.1f}%. Chứng chỉ đang chờ admin duyệt.", ocr_data

