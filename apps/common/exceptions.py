from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessLogicError(APIException):
    """
    خطای منطق کسب‌وکار
    وقتی عملیات از نظر فنی درست است
    ولی از نظر کسب‌وکار مجاز نیست.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "business_logic_error"

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)


class OutOfStackError(BusinessLogicError):
    """
    موجودی کافی نیست
    """
    default_detail = 'موجودی کافی نیست'
    default_code = 'OUT_OF_STOCK'


class InvalidCouponError(BusinessLogicError):
    """
    کد تخفیف نامعتبر
    """
    default_detail = 'کد تخفیف معتبر نیست'
    default_code = 'INVALID_COUPON'


class PaymentError(BusinessLogicError):
    """
    خطا در پرداخت
    """
    default_detail = 'خطا در پرداخت'
    default_code = 'PAYMENT_ERROR'


class AccountSuspendedError(APIException):
    """
    حساب معلق
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'حساب کاربری شما به حالت تعلیق درآمده'
    default_code = 'ACCOUNT_SUSPENDED'


class  AccountBlockedError(APIException):
    """
    حساب مسدود
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'حساب کاربری شما مسدود شده است'
    default_code = "ACCOUNT_BLOCKED"