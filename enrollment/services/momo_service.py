"""
MoMo Payment Gateway Integration
"""
import json
import hmac
import hashlib
import requests
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
from django.conf import settings
from .payment_gateway import PaymentGatewayService
import logging

logger = logging.getLogger(__name__)


class MoMoService(PaymentGatewayService):
    """
    MoMo Payment Gateway Service
    Documentation: https://developers.momo.vn/
    """
    
    def __init__(self):
        self.partner_code = getattr(settings, 'MOMO_PARTNER_CODE', '')
        self.access_key = getattr(settings, 'MOMO_ACCESS_KEY', '')
        self.secret_key = getattr(settings, 'MOMO_SECRET_KEY', '')
        self.endpoint = getattr(settings, 'MOMO_ENDPOINT', 'https://test-payment.momo.vn/v2/gateway/api/create')
        self.return_url = getattr(settings, 'MOMO_RETURN_URL', 'http://localhost:8000/api/enrollment/payments/momo/return/')
        self.notify_url = getattr(settings, 'MOMO_NOTIFY_URL', 'http://localhost:8000/api/enrollment/payments/momo/notify/')
        
    def _create_signature(self, data: dict) -> str:
        """Tạo chữ ký cho MoMo"""
        # Sort data by key
        sorted_data = sorted(data.items())
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_data])
        
        # Create HMAC SHA256
        hmac_obj = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        )
        return hmac_obj.hexdigest()
    
    def create_payment_url(self, amount: Decimal, order_id: str, order_info: str,
                          return_url: Optional[str] = None, **kwargs) -> Dict[str, any]:
        """
        Tạo payment URL cho MoMo
        """
        try:
            # Convert amount to VND
            amount_vnd = int(amount)
            
            # Prepare request data
            request_data = {
                'partnerCode': self.partner_code,
                'partnerName': kwargs.get('partner_name', 'English Center'),
                'storeId': kwargs.get('store_id', 'EnglishCenter'),
                'requestId': order_id,
                'amount': amount_vnd,
                'orderId': order_id,
                'orderInfo': order_info,
                'redirectUrl': return_url or self.return_url,
                'ipnUrl': self.notify_url,
                'lang': 'vi',
                'extraData': kwargs.get('extra_data', ''),
                'requestType': 'captureWallet',
                'autoCapture': True,
            }
            
            # Create signature
            request_data['signature'] = self._create_signature(request_data)
            
            # Call MoMo API
            response = requests.post(self.endpoint, json=request_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('resultCode') == 0:
                    return {
                        'success': True,
                        'payment_url': result.get('payUrl'),
                        'transaction_id': order_id,
                        'expires_at': datetime.now() + timedelta(minutes=15),
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'MoMo payment creation failed'),
                    }
            else:
                return {
                    'success': False,
                    'error': f'MoMo API error: {response.status_code}',
                }
                
        except Exception as e:
            logger.error(f"MoMo create_payment_url error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def verify_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Verify payment từ MoMo callback
        """
        try:
            # Get data from callback
            result_code = kwargs.get('resultCode')
            order_id = kwargs.get('orderId')
            signature = kwargs.get('signature', '')
            
            # Verify signature
            verify_data = {k: v for k, v in kwargs.items() if k != 'signature'}
            calculated_signature = self._create_signature(verify_data)
            
            if calculated_signature != signature:
                return {
                    'success': False,
                    'status': 'failed',
                    'message': 'Invalid signature',
                }
            
            # Check result code
            # 0 = Success
            if result_code == 0:
                return {
                    'success': True,
                    'transaction_id': transaction_id or order_id,
                    'amount': amount,
                    'status': 'success',
                    'message': 'Thanh toán thành công',
                }
            else:
                error_messages = {
                    '1001': 'Thẻ/Tài khoản không hợp lệ',
                    '1002': 'Số dư không đủ',
                    '1003': 'Giao dịch bị từ chối',
                    '1004': 'Giao dịch đã tồn tại',
                    '1005': 'Giao dịch không tồn tại',
                    '1006': 'Giao dịch đã hết hạn',
                }
                
                return {
                    'success': False,
                    'transaction_id': transaction_id or order_id,
                    'status': 'failed',
                    'message': error_messages.get(str(result_code), f'Mã lỗi: {result_code}'),
                }
                
        except Exception as e:
            logger.error(f"MoMo verify_payment error: {str(e)}")
            return {
                'success': False,
                'status': 'failed',
                'message': str(e),
            }
    
    def refund(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Hoàn tiền qua MoMo
        """
        # TODO: Implement MoMo refund API
        logger.warning("MoMo refund not implemented yet")
        return {
            'success': False,
            'message': 'MoMo refund chưa được implement',
        }


