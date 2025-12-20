"""
VNPay Payment Gateway Integration
"""
import hmac
import hashlib
import urllib.parse
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.urls import reverse
from .payment_gateway import PaymentGatewayService
import logging

logger = logging.getLogger(__name__)


class VNPayService(PaymentGatewayService):
    """
    VNPay Payment Gateway Service
    Documentation: https://sandbox.vnpayment.vn/apis/docs/
    """
    
    def __init__(self):
        # Lấy config từ settings hoặc environment variables
        self.tmn_code = getattr(settings, 'VNPAY_TMN_CODE', '')
        self.secret_key = getattr(settings, 'VNPAY_SECRET_KEY', '')
        self.url = getattr(settings, 'VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
        self.return_url = getattr(settings, 'VNPAY_RETURN_URL', 'http://localhost:8000/api/enrollment/payments/vnpay/return/')
        
    def _create_secure_hash(self, data: dict) -> str:
        """Tạo secure hash cho VNPay"""
        # Sort data by key
        sorted_data = sorted(data.items())
        query_string = urllib.parse.urlencode(sorted_data)
        
        # Create HMAC SHA512
        hmac_obj = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        )
        return hmac_obj.hexdigest()
    
    def create_payment_url(self, amount: Decimal, order_id: str, order_info: str,
                          return_url: Optional[str] = None, **kwargs) -> Dict[str, any]:
        """
        Tạo payment URL cho VNPay
        
        Args:
            amount: Số tiền (VND)
            order_id: Mã đơn hàng (unique)
            order_info: Thông tin đơn hàng
            return_url: URL để redirect sau khi thanh toán
        """
        try:
            # Convert amount to VND (VNPay uses VND)
            amount_vnd = int(amount * 100)  # VNPay expects amount in cents
            
            # Prepare payment data
            vnp_data = {
                'vnp_Version': '2.1.0',
                'vnp_Command': 'pay',
                'vnp_TmnCode': self.tmn_code,
                'vnp_Amount': str(amount_vnd),
                'vnp_CurrCode': 'VND',
                'vnp_TxnRef': order_id,
                'vnp_OrderInfo': order_info[:255],  # Max 255 chars
                'vnp_OrderType': 'other',
                'vnp_Locale': 'vn',
                'vnp_ReturnUrl': return_url or self.return_url,
                'vnp_IpAddr': kwargs.get('ip_address', '127.0.0.1'),
                'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
            }
            
            # Add expiration date (optional, default 15 minutes)
            expire_date = kwargs.get('expires_at')
            if expire_date:
                vnp_data['vnp_ExpireDate'] = expire_date.strftime('%Y%m%d%H%M%S')
            
            # Create secure hash
            vnp_data['vnp_SecureHash'] = self._create_secure_hash(vnp_data)
            
            # Build payment URL
            payment_url = f"{self.url}?{urllib.parse.urlencode(vnp_data)}"
            
            return {
                'success': True,
                'payment_url': payment_url,
                'transaction_id': order_id,
                'expires_at': expire_date or (datetime.now() + timedelta(minutes=15)),
            }
            
        except Exception as e:
            logger.error(f"VNPay create_payment_url error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Verify payment từ VNPay callback
        
        Args:
            transaction_id: Mã giao dịch từ VNPay
            amount: Số tiền cần verify
            **kwargs: Các tham số từ VNPay callback (vnp_ResponseCode, vnp_SecureHash, etc.)
        """
        try:
            # Get response code from VNPay
            response_code = kwargs.get('vnp_ResponseCode', '')
            vnp_secure_hash = kwargs.get('vnp_SecureHash', '')
            
            # Verify secure hash
            vnp_data = {k: v for k, v in kwargs.items() if k.startswith('vnp_') and k != 'vnp_SecureHash'}
            calculated_hash = self._create_secure_hash(vnp_data)
            
            if calculated_hash != vnp_secure_hash:
                return {
                    'success': False,
                    'status': 'failed',
                    'message': 'Invalid secure hash',
                }
            
            # Check response code
            # 00 = Success
            if response_code == '00':
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'status': 'success',
                    'message': 'Thanh toán thành công',
                }
            else:
                error_messages = {
                    '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường).',
                    '09': 'Thẻ/Tài khoản chưa đăng ký dịch vụ InternetBanking',
                    '10': 'Xác thực thông tin thẻ/tài khoản không đúng. Quá 3 lần',
                    '11': 'Đã hết hạn chờ thanh toán. Xin vui lòng thực hiện lại giao dịch',
                    '12': 'Thẻ/Tài khoản bị khóa.',
                    '13': 'Nhập sai mật khẩu xác thực giao dịch (OTP). Quá 5 lần',
                    '51': 'Tài khoản không đủ số dư để thực hiện giao dịch.',
                    '65': 'Tài khoản đã vượt quá hạn mức giao dịch trong ngày.',
                    '75': 'Ngân hàng thanh toán đang bảo trì.',
                    '79': 'Nhập sai mật khẩu thanh toán quá số lần quy định.',
                }
                
                return {
                    'success': False,
                    'transaction_id': transaction_id,
                    'status': 'failed',
                    'message': error_messages.get(response_code, f'Mã lỗi: {response_code}'),
                }
                
        except Exception as e:
            logger.error(f"VNPay verify_payment error: {str(e)}")
            return {
                'success': False,
                'status': 'failed',
                'message': str(e),
            }
    
    def refund(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Hoàn tiền qua VNPay
        Note: Cần implement API call đến VNPay refund endpoint
        """
        # TODO: Implement VNPay refund API
        logger.warning("VNPay refund not implemented yet")
        return {
            'success': False,
            'message': 'VNPay refund chưa được implement',
        }


