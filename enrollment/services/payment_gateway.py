"""
Base class cho payment gateway services
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PaymentGatewayService(ABC):
    """Base class cho tất cả payment gateway services"""
    
    @abstractmethod
    def create_payment_url(self, amount: Decimal, order_id: str, order_info: str, 
                          return_url: str, **kwargs) -> Dict[str, any]:
        """
        Tạo payment URL để redirect user đến trang thanh toán
        
        Returns:
            {
                'payment_url': 'https://...',
                'transaction_id': '...',
                'expires_at': datetime,
            }
        """
        pass
    
    @abstractmethod
    def verify_payment(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Verify payment sau khi user thanh toán xong
        
        Returns:
            {
                'success': True/False,
                'transaction_id': '...',
                'amount': Decimal,
                'status': 'success'/'failed',
                'message': '...',
            }
        """
        pass
    
    @abstractmethod
    def refund(self, transaction_id: str, amount: Decimal, **kwargs) -> Dict[str, any]:
        """
        Hoàn tiền
        
        Returns:
            {
                'success': True/False,
                'refund_id': '...',
                'message': '...',
            }
        """
        pass


