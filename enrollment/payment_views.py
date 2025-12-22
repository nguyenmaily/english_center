"""
VNPay Payment Callback Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Enrollment
from .payment_gateway import VNPayGateway
import logging

logger = logging.getLogger(__name__)


class VNPayReturnView(APIView):
    """
    GET /api/enrollment/payments/vnpay/return/
    
    VNPay return URL - Sau khi thanh toán, VNPay redirect về đây
    """
    permission_classes = [AllowAny]  # VNPay sẽ gọi từ bên ngoài
    
    def get(self, request):
        """
        Xử lý return từ VNPay
        
        Query params từ VNPay:
        - vnp_Amount: Số tiền (đã nhân 100)
        - vnp_BankCode: Mã ngân hàng
        - vnp_BankTranNo: Mã giao dịch ngân hàng
        - vnp_CardType: Loại thẻ
        - vnp_OrderInfo: Mô tả đơn hàng
        - vnp_PayDate: Ngày thanh toán
        - vnp_ResponseCode: Mã phản hồi (00 = thành công)
        - vnp_TmnCode: Mã merchant
        - vnp_TransactionNo: Mã giao dịch VNPay
        - vnp_TxnRef: Mã đơn hàng (enrollment_id)
        - vnp_SecureHash: Hash để verify
        """
        # Lấy tất cả params từ VNPay
        vnp_params = dict(request.query_params)
        # Convert từ QueryDict sang dict thông thường
        vnp_params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v 
                      for k, v in vnp_params.items()}
        
        # Verify payment
        gateway = VNPayGateway()
        is_valid, response_code, transaction_id, amount = gateway.verify_payment_response(vnp_params)
        
        if not is_valid:
            logger.error(f"Invalid VNPay hash in return URL")
            return Response({
                'success': False,
                'error': 'Invalid payment signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy enrollment_id từ vnp_TxnRef
        # vnp_TxnRef đã bị loại bỏ dấu gạch ngang khi tạo payment URL
        # Cần thêm lại dấu gạch ngang để tạo UUID hợp lệ
        txn_ref = vnp_params.get('vnp_TxnRef', '')
        if not txn_ref:
            return Response({
                'success': False,
                'error': 'Missing order ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Thêm lại dấu gạch ngang vào UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        # UUID có độ dài 32 ký tự (không có dấu gạch ngang)
        if len(txn_ref) == 32:
            enrollment_id = f"{txn_ref[:8]}-{txn_ref[8:12]}-{txn_ref[12:16]}-{txn_ref[16:20]}-{txn_ref[20:]}"
        else:
            # Nếu không đúng format, thử dùng trực tiếp
            enrollment_id = txn_ref
        
        logger.info(f"VNPay return - TxnRef: {txn_ref}, Enrollment ID: {enrollment_id}")
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            logger.error(f"Enrollment not found for ID: {enrollment_id} (from TxnRef: {txn_ref})")
            return Response({
                'success': False,
                'error': f'Enrollment not found (ID: {enrollment_id})'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra response code
        # 00 = thành công
        if response_code == '00':
            # Cập nhật invoice_status
            enrollment.invoice_status = 'paid'
            enrollment.save(update_fields=['invoice_status', 'updated_at'])
            
            logger.info(f"Payment successful for enrollment {enrollment_id}, transaction {transaction_id}")
            
            return Response({
                'success': True,
                'message': 'Thanh toán thành công',
                'data': {
                    'enrollment_id': str(enrollment.id),
                    'invoice_status': enrollment.invoice_status,
                    'transaction_id': transaction_id,
                    'amount': float(amount)
                }
            })
        else:
            # Thanh toán thất bại
            logger.warning(f"Payment failed for enrollment {enrollment_id}, response_code: {response_code}")
            
            return Response({
                'success': False,
                'error': 'Thanh toán thất bại',
                'response_code': response_code
            }, status=status.HTTP_400_BAD_REQUEST)


class VNPayIPNView(APIView):
    """
    POST /api/enrollment/payments/vnpay/notify/
    
    VNPay IPN (Instant Payment Notification) URL - VNPay gọi để notify về kết quả thanh toán
    """
    permission_classes = [AllowAny]  # VNPay sẽ gọi từ bên ngoài
    
    def post(self, request):
        """
        Xử lý IPN từ VNPay
        
        Body params từ VNPay (giống như return URL)
        """
        # Lấy tất cả params từ VNPay
        vnp_params = dict(request.data)
        # Convert từ QueryDict sang dict thông thường
        vnp_params = {k: v[0] if isinstance(v, list) and len(v) > 0 else v 
                      for k, v in vnp_params.items()}
        
        # Verify payment
        gateway = VNPayGateway()
        is_valid, response_code, transaction_id, amount = gateway.verify_payment_response(vnp_params)
        
        if not is_valid:
            logger.error(f"Invalid VNPay hash in IPN URL")
            return Response({
                'RspCode': '97',
                'Message': 'Invalid signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy enrollment_id từ vnp_TxnRef
        # vnp_TxnRef đã bị loại bỏ dấu gạch ngang khi tạo payment URL
        # Cần thêm lại dấu gạch ngang để tạo UUID hợp lệ
        txn_ref = vnp_params.get('vnp_TxnRef', '')
        if not txn_ref:
            return Response({
                'RspCode': '99',
                'Message': 'Missing order ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Thêm lại dấu gạch ngang vào UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        # UUID có độ dài 32 ký tự (không có dấu gạch ngang)
        if len(txn_ref) == 32:
            enrollment_id = f"{txn_ref[:8]}-{txn_ref[8:12]}-{txn_ref[12:16]}-{txn_ref[16:20]}-{txn_ref[20:]}"
        else:
            # Nếu không đúng format, thử dùng trực tiếp
            enrollment_id = txn_ref
        
        logger.info(f"VNPay IPN - TxnRef: {txn_ref}, Enrollment ID: {enrollment_id}")
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            logger.error(f"Enrollment not found for ID: {enrollment_id} (from TxnRef: {txn_ref})")
            return Response({
                'RspCode': '01',
                'Message': f'Order not found (ID: {enrollment_id})'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra response code
        # 00 = thành công
        if response_code == '00':
            # Cập nhật invoice_status
            enrollment.invoice_status = 'paid'
            enrollment.save(update_fields=['invoice_status', 'updated_at'])
            
            logger.info(f"Payment successful (IPN) for enrollment {enrollment_id}, transaction {transaction_id}")
            
            # Trả về response cho VNPay
            return Response({
                'RspCode': '00',
                'Message': 'Success'
            })
        else:
            # Thanh toán thất bại
            logger.warning(f"Payment failed (IPN) for enrollment {enrollment_id}, response_code: {response_code}")
            
            return Response({
                'RspCode': response_code,
                'Message': 'Payment failed'
            })


class VNPayTestReturnView(APIView):
    """
    GET /api/enrollment/payments/vnpay/test-return/
    
    Test endpoint để simulate VNPay return callback (chỉ dùng trong development)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Simulate VNPay return callback để test payment flow
        
        Query params:
        - enrollment_id: UUID của enrollment cần test
        - success: true/false (mặc định: true)
        """
        from django.conf import settings
        
        # Chỉ cho phép trong DEBUG mode
        if not settings.DEBUG:
            return Response({
                'success': False,
                'error': 'Test endpoint chỉ khả dụng trong DEBUG mode'
            }, status=status.HTTP_403_FORBIDDEN)
        
        enrollment_id = request.query_params.get('enrollment_id')
        success = request.query_params.get('success', 'true').lower() == 'true'
        
        if not enrollment_id:
            return Response({
                'success': False,
                'error': 'enrollment_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Enrollment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if success:
            # Simulate successful payment
            enrollment.invoice_status = 'paid'
            enrollment.save(update_fields=['invoice_status', 'updated_at'])
            
            logger.info(f"Test payment successful for enrollment {enrollment_id}")
            
            return Response({
                'success': True,
                'message': 'Thanh toán thành công (Test)',
                'data': {
                    'enrollment_id': str(enrollment.id),
                    'invoice_status': enrollment.invoice_status,
                    'transaction_id': 'TEST_' + str(int(timezone.now().timestamp())),
                    'amount': float(enrollment.amount) if hasattr(enrollment, 'amount') else 0
                }
            })
        else:
            # Simulate failed payment
            logger.warning(f"Test payment failed for enrollment {enrollment_id}")
            
            return Response({
                'success': False,
                'error': 'Thanh toán thất bại (Test)',
                'response_code': '07'
            }, status=status.HTTP_400_BAD_REQUEST)


