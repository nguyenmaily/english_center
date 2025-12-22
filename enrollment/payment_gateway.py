"""
VNPay Payment Gateway Integration
"""
import hmac
import hashlib
import urllib.parse
import logging
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class VNPayGateway:
    """
    VNPay Payment Gateway Integration
    
    Cần cấu hình trong settings.py:
    VNPAY_TMN_CODE = 'your_tmn_code'
    VNPAY_HASH_SECRET = 'your_hash_secret'
    VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'  # Sandbox
    # VNPAY_URL = 'https://www.vnpayment.vn/paymentv2/vpcpay.html'  # Production
    VNPAY_RETURN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/return/'
    VNPAY_IPN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/notify/'
    """
    
    def __init__(self):
        self.tmn_code = getattr(settings, 'VNPAY_TMN_CODE', '').strip()
        self.hash_secret = getattr(settings, 'VNPAY_HASH_SECRET', '').strip()
        self.vnpay_url = getattr(settings, 'VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
        self.return_url = getattr(settings, 'VNPAY_RETURN_URL', '').strip()
        self.ipn_url = getattr(settings, 'VNPAY_IPN_URL', '').strip()
        
        # Log để debug
        logger.debug(f"VNPay Gateway initialized - TMN_CODE: {self.tmn_code[:5]}..., HASH_SECRET: {'***' if self.hash_secret else 'EMPTY'}, RETURN_URL: {self.return_url}")
    
    def create_payment_url(self, order_id, amount, order_desc='', order_type='other', 
                          bank_code='', locale='vn', ipaddr='', **kwargs):
        """
        Tạo payment URL từ VNPay
        
        Args:
            order_id: Mã đơn hàng (enrollment_id)
            amount: Số tiền (VND)
            order_desc: Mô tả đơn hàng
            order_type: Loại đơn hàng
            bank_code: Mã ngân hàng (optional)
            locale: Ngôn ngữ (vn, en)
            ipaddr: IP của khách hàng
            **kwargs: Các tham số khác
        
        Returns:
            str: Payment URL
        """
        from datetime import datetime
        
        # Đảm bảo create_date luôn có giá trị
        create_date = kwargs.get('create_date', '')
        if not create_date:
            create_date = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Convert amount sang số nguyên (VNPay yêu cầu amount * 100)
        # Xử lý Decimal, float, hoặc int
        try:
            if isinstance(amount, str):
                amount = float(amount)
            amount_int = int(float(amount) * 100)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid amount format: {amount}, error: {e}")
            raise ValueError(f"Invalid amount format: {amount}")
        
        # Đảm bảo order_desc không rỗng và không có ký tự đặc biệt
        if not order_desc:
            order_desc = f'Thanh toan dang ky lop hoc'
        # Loại bỏ ký tự đặc biệt và giới hạn độ dài
        # VNPay yêu cầu order_desc chỉ chứa chữ cái, số, và một số ký tự đặc biệt
        import re
        order_desc = re.sub(r'[^\w\s-]', '', order_desc)  # Chỉ giữ chữ, số, khoảng trắng, dấu gạch ngang
        order_desc = order_desc[:255]  # VNPay giới hạn 255 ký tự
        
        # Đảm bảo vnp_TxnRef không quá dài (VNPay giới hạn 100 ký tự)
        txn_ref = str(order_id).replace('-', '')[:100]  # Loại bỏ dấu gạch ngang và giới hạn độ dài
        
        # Validate các tham số bắt buộc
        if not self.tmn_code:
            raise ValueError("VNPAY_TMN_CODE is not configured")
        if not self.hash_secret:
            raise ValueError("VNPAY_HASH_SECRET is not configured")
        if not self.return_url:
            raise ValueError("VNPAY_RETURN_URL is not configured")
        
        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.tmn_code,
            'vnp_Amount': amount_int,  # VNPay yêu cầu số nguyên (không phải string)
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': txn_ref,
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': order_type,
            'vnp_Locale': locale,
            'vnp_ReturnUrl': self.return_url,
            'vnp_IpAddr': ipaddr or '127.0.0.1',
            'vnp_CreateDate': create_date,
        }
        
        # Thêm bank_code nếu có (chỉ thêm nếu không rỗng)
        if bank_code and bank_code.strip():
            vnp_params['vnp_BankCode'] = bank_code.strip()
        
        # Loại bỏ các params rỗng trước khi tạo hash
        vnp_params = {k: v for k, v in vnp_params.items() if v is not None and v != ''}
        
        # Sắp xếp params theo thứ tự alphabet
        # VNPay yêu cầu tất cả giá trị phải là string khi encode
        vnp_params_sorted = sorted([(k, str(v)) for k, v in vnp_params.items()])
        
        # Tạo query string
        query_string = urllib.parse.urlencode(vnp_params_sorted)
        
        # Tạo secure hash
        secure_hash = self._create_secure_hash(query_string)
        
        # Thêm secure hash vào query string
        query_string += f'&vnp_SecureHash={secure_hash}'
        
        # Tạo payment URL
        payment_url = f'{self.vnpay_url}?{query_string}'
        
        logger.info(f"Created VNPay payment URL for order {order_id}, amount {amount} (VNPay amount: {amount_int})")
        logger.debug(f"VNPay params: {vnp_params}")
        
        return payment_url
    
    def _create_secure_hash(self, query_string):
        """
        Tạo secure hash từ query string
        
        Args:
            query_string: Query string đã được sắp xếp
        
        Returns:
            str: Secure hash (SHA256)
        """
        # Loại bỏ vnp_SecureHash và vnp_SecureHashType nếu có
        query_string = query_string.replace('&vnp_SecureHash=', '')
        query_string = query_string.replace('&vnp_SecureHashType=', '')
        
        # Tạo HMAC SHA512
        hmac_sha512 = hmac.new(
            bytes(self.hash_secret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac_sha512
    
    def verify_payment_response(self, vnp_params):
        """
        Verify payment response từ VNPay
        
        Args:
            vnp_params: Dict chứa các params từ VNPay callback
        
        Returns:
            tuple: (is_valid, response_code, transaction_id, amount)
        """
        # Lấy secure hash từ params
        secure_hash = vnp_params.pop('vnp_SecureHash', '')
        secure_hash_type = vnp_params.pop('vnp_SecureHashType', 'SHA256')
        
        # Sắp xếp params
        vnp_params_sorted = sorted(vnp_params.items())
        
        # Tạo query string
        query_string = urllib.parse.urlencode(vnp_params_sorted)
        
        # Tạo secure hash để verify
        calculated_hash = self._create_secure_hash(query_string)
        
        # Verify hash
        is_valid = secure_hash == calculated_hash
        
        if not is_valid:
            logger.warning(f"Invalid VNPay hash. Expected: {calculated_hash}, Got: {secure_hash}")
            return False, None, None, None
        
        # Lấy thông tin từ response
        response_code = vnp_params.get('vnp_ResponseCode', '')
        transaction_id = vnp_params.get('vnp_TransactionNo', '')
        amount = vnp_params.get('vnp_Amount', 0)
        
        # Convert amount về VND (chia cho 100)
        amount_vnd = int(amount) / 100 if amount else 0
        
        return is_valid, response_code, transaction_id, amount_vnd


def create_vnpay_payment_url(enrollment_id, amount, request=None):
    """
    Helper function để tạo VNPay payment URL
    
    Args:
        enrollment_id: UUID của enrollment
        amount: Số tiền (VND)
        request: Django request object (để lấy IP)
    
    Returns:
        str: Payment URL
    
    Raises:
        ValueError: Nếu thiếu cấu hình VNPay
    """
    try:
        gateway = VNPayGateway()
        
        # Validate settings
        if not gateway.tmn_code:
            raise ValueError("VNPAY_TMN_CODE chưa được cấu hình. Vui lòng thêm vào .env hoặc settings.py")
        if not gateway.hash_secret:
            raise ValueError("VNPAY_HASH_SECRET chưa được cấu hình. Vui lòng thêm vào .env hoặc settings.py")
        if not gateway.return_url:
            raise ValueError("VNPAY_RETURN_URL chưa được cấu hình. Vui lòng thêm vào .env hoặc settings.py")
        
        # Lấy IP từ request
        ipaddr = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ipaddr = x_forwarded_for.split(',')[0]
            else:
                ipaddr = request.META.get('REMOTE_ADDR')
        
        # Tạo payment URL
        from datetime import datetime
        create_date = datetime.now().strftime('%Y%m%d%H%M%S')
        
        logger.info(f"Creating VNPay payment URL for enrollment {enrollment_id}, amount {amount}")
        
        payment_url = gateway.create_payment_url(
            order_id=str(enrollment_id),
            amount=float(amount),
            order_desc=f'Thanh toan dang ky lop hoc - {enrollment_id}',
            order_type='other',
            locale='vn',
            ipaddr=ipaddr or '127.0.0.1',
            create_date=create_date
        )
        
        logger.info(f"VNPay payment URL created successfully: {payment_url[:100]}...")
        return payment_url
        
    except ValueError as e:
        logger.error(f"VNPay configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating VNPay payment URL: {str(e)}", exc_info=True)
        raise ValueError(f"Lỗi khi tạo payment URL: {str(e)}")


