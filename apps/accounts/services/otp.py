from django.db import transaction

from accounts.models import OTPCode


class OTPError(Exception):
    """Base exception for OTP verification errors."""


class OTPNotFound(OTPError):
    """OTP does not exist."""


class OTPExpired(OTPError):
    """OTP has expired."""


class OTPAlreadyUsed(OTPError):
    """OTP has already been consumed."""


class OTPMaxAttemptsReached(OTPError):
    """Maximum verification attempts have been reached."""


class OTPInvalidCode(OTPError):
    """Provided OTP code is incorrect."""


class OTPService:
    """
    Handles OTP verification safely and atomically.

    The OTP row is locked during verification to prevent multiple
    concurrent requests from consuming the same OTP.
    """

    @staticmethod
    @transaction.atomic
    def verify(*, otp_id, code: str) -> OTPCode:
        """
        Verify and consume an OTP.

        Flow:
            1. Lock OTP row.
            2. Check whether it exists.
            3. Check whether it has already been used.
            4. Check expiration.
            5. Check maximum attempts.
            6. Verify the submitted code.
            7. Increment attempts if the code is incorrect.
            8. Consume OTP if verification succeeds.

        Returns:
            OTPCode:
                The verified and consumed OTP instance.

        Raises:
            OTPNotFound:
                If the OTP does not exist.

            OTPAlreadyUsed:
                If the OTP has already been consumed.

            OTPExpired:
                If the OTP has expired.

            OTPMaxAttemptsReached:
                If the maximum attempts limit has been reached.

            OTPInvalidCode:
                If the submitted OTP code is incorrect.
        """

        try:
            otp = (
                OTPCode.objects
                .select_for_update()
                .get(id=otp_id)
            )
        except OTPCode.DoesNotExist:
            raise OTPNotFound("OTP not found.")

        if otp.is_used:
            raise OTPAlreadyUsed("OTP has already been used.")

        if otp.is_expired:
            raise OTPExpired("OTP has expired.")

        if otp.is_max_attempts_reached:
            raise OTPMaxAttemptsReached(
                "Maximum OTP attempts reached."
            )

        if not otp.check_code(code):
            otp.increment_attempts()
            raise OTPInvalidCode("Invalid OTP code.")

        otp.consume()

        return otp