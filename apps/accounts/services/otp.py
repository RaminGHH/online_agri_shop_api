import re
import secrets

from datetime import timedelta
from typing import Callable

from django.db import transaction
from django.utils import timezone

from accounts.models import OTPCode


# =========================================================
# Exceptions
# =========================================================


class OTPError(Exception):
    """
    Base exception for all OTP-related errors.
    """


class OTPInvalidPhone(OTPError):
    """
    Phone number format is invalid.
    """


class OTPInvalidPurpose(OTPError):
    """
    OTP purpose is invalid.
    """


class OTPCooldownError(OTPError):
    """
    A new OTP was requested before resend cooldown expired.
    """

    def __init__(self, remaining_seconds: int):
        self.remaining_seconds = remaining_seconds

        super().__init__(
            f"Please wait {remaining_seconds} seconds "
            f"before requesting another OTP."
        )


class OTPRateLimitError(OTPError):
    """
    Too many OTP requests were made in the rate-limit window.
    """


class OTPNotFound(OTPError):
    """
    No active OTP exists for the given phone and purpose.
    """


class OTPExpired(OTPError):
    """
    OTP has expired.
    """


class OTPMaxAttemptsReached(OTPError):
    """
    Maximum OTP verification attempts have been reached.
    """


class OTPInvalidCode(OTPError):
    """
    Submitted OTP code is incorrect.
    """

    def __init__(self, remaining_attempts: int):
        self.remaining_attempts = remaining_attempts

        super().__init__(
            f"Invalid OTP code. "
            f"{remaining_attempts} attempts remaining."
        )


class OTPDeliveryError(OTPError):
    """
    OTP was generated but SMS delivery failed.
    """


# =========================================================
# OTP Service
# =========================================================


class OTPService:
    """
    Service responsible for OTP creation and verification.

    Rules:
        - OTP length: 6 digits
        - OTP lifetime: 5 minutes
        - Resend cooldown: 60 seconds
        - Maximum requests: 5 per 5 minutes
        - Maximum verification attempts: 3
        - Only one active OTP per phone/purpose
        - OTP verification is concurrency-safe
    """

    CODE_LENGTH = 6

    OTP_LIFETIME = timedelta(minutes=5)

    RESEND_COOLDOWN = timedelta(seconds=60)

    RATE_LIMIT_WINDOW = timedelta(minutes=5)

    MAX_REQUESTS_PER_WINDOW = 5

    MAX_ATTEMPTS = 3

    # =====================================================
    # Phone
    # =====================================================

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize an Iranian mobile number.

        Supported input examples:
            09123456789
            +989123456789
            989123456789
        """

        if phone is None:
            raise OTPInvalidPhone(
                "Phone number is required."
            )

        phone = (
            str(phone)
            .strip()
            .replace(" ", "")
            .replace("-", "")
        )

        if phone.startswith("+98"):
            phone = "0" + phone[3:]

        elif phone.startswith("98"):
            phone = "0" + phone[2:]

        if not re.fullmatch(r"09\d{9}", phone):
            raise OTPInvalidPhone(
                "Invalid Iranian mobile number."
            )

        return phone

    # =====================================================
    # Purpose
    # =====================================================

    @staticmethod
    def validate_purpose(purpose: str) -> str:
        """
        Validate OTP purpose.
        """

        if purpose not in OTPCode.Purpose.values:
            raise OTPInvalidPurpose(
                "Invalid OTP purpose."
            )

        return purpose

    # =====================================================
    # Code generation
    # =====================================================

    @classmethod
    def generate_code(cls) -> str:
        """
        Generate a cryptographically secure 6-digit OTP.

        Leading zeros are preserved.

        Example:
            004281
        """

        upper_bound = 10 ** cls.CODE_LENGTH

        number = secrets.randbelow(
            upper_bound
        )

        return str(number).zfill(
            cls.CODE_LENGTH
        )

    # =====================================================
    # SEND
    # =====================================================

    @classmethod
    def send(
        cls,
        *,
        phone: str,
        purpose: str,
        sms_sender: Callable[[str, str, str], None],
    ) -> OTPCode:
        """
        Generate, store and send a new OTP.

        Args:
            phone:
                User mobile number.

            purpose:
                OTP purpose.

            sms_sender:
                Callable responsible for sending the SMS.

                Signature:

                    sms_sender(phone, code, purpose)

        Flow:
            1. Normalize phone.
            2. Validate purpose.
            3. Check 60-second resend cooldown.
            4. Check 5 requests / 5 minutes rate limit.
            5. Invalidate previous active OTP.
            6. Generate secure OTP.
            7. Store hashed OTP.
            8. Send plain OTP through SMS provider.

        Returns:
            Created OTPCode object.
        """

        phone = cls.normalize_phone(phone)

        purpose = cls.validate_purpose(
            purpose
        )

        now = timezone.now()

        # =============================================
        # Database operations
        # =============================================

        with transaction.atomic():

            # Lock previous OTP rows for this phone/purpose.
            existing_otps = (
                OTPCode.objects
                .select_for_update()
                .filter(
                    phone=phone,
                    purpose=purpose,
                )
            )

            latest_otp = (
                existing_otps
                .order_by("-created_at")
                .first()
            )

            # -----------------------------------------
            # Resend cooldown
            # -----------------------------------------

            if latest_otp is not None:

                cooldown_until = (
                    latest_otp.created_at
                    + cls.RESEND_COOLDOWN
                )

                if now < cooldown_until:

                    remaining = int(
                        (
                            cooldown_until
                            - now
                        ).total_seconds()
                    )

                    # Never return 0 while cooldown exists.
                    remaining = max(
                        remaining,
                        1,
                    )

                    raise OTPCooldownError(
                        remaining_seconds=remaining
                    )

            # -----------------------------------------
            # Rate limit
            # Max 5 requests in 5 minutes
            # -----------------------------------------

            window_start = (
                now
                - cls.RATE_LIMIT_WINDOW
            )

            request_count = (
                OTPCode.objects
                .filter(
                    phone=phone,
                    purpose=purpose,
                    created_at__gte=window_start,
                )
                .count()
            )

            if (
                request_count
                >= cls.MAX_REQUESTS_PER_WINDOW
            ):
                raise OTPRateLimitError(
                    "Maximum OTP requests reached. "
                    "Try again later."
                )

            # -----------------------------------------
            # Invalidate previous active OTP
            # -----------------------------------------

            existing_otps.filter(
                is_used=False
            ).update(
                is_used=True
            )

            # -----------------------------------------
            # Generate OTP
            # -----------------------------------------

            code = cls.generate_code()

            expires_at = (
                now
                + cls.OTP_LIFETIME
            )

            # -----------------------------------------
            # Store OTP
            # -----------------------------------------

            otp = OTPCode.objects.create(
                phone=phone,
                purpose=purpose,
                code_hash=OTPCode.make_hash(
                    code
                ),
                attempts=0,
                max_attempts=cls.MAX_ATTEMPTS,
                expires_at=expires_at,
            )

        # =============================================
        # Send SMS
        #
        # Do this outside the database transaction.
        # We do not want to hold a DB lock while waiting
        # for an external SMS provider.
        # =============================================

        try:

            sms_sender(
                phone,
                code,
                purpose,
            )

        except Exception as exc:

            # The user never received this OTP,
            # so disable it.
            OTPCode.objects.filter(
                pk=otp.pk
            ).update(
                is_used=True
            )

            raise OTPDeliveryError(
                "Failed to deliver OTP."
            ) from exc

        return otp

    # =====================================================
    # VERIFY
    # =====================================================

    @classmethod
    def verify(
        cls,
        *,
        phone: str,
        purpose: str,
        code: str,
    ) -> OTPCode:
        """
        Verify and consume an OTP safely.

        This operation uses SELECT FOR UPDATE to prevent
        two concurrent requests from consuming the same OTP.

        Flow:
            1. Normalize phone.
            2. Validate purpose.
            3. Lock latest active OTP.
            4. Check expiration.
            5. Check attempts.
            6. Verify submitted code.
            7. Increase attempts if incorrect.
            8. Consume OTP if correct.

        Returns:
            Verified OTPCode instance.

        Raises:
            OTPNotFound
            OTPExpired
            OTPMaxAttemptsReached
            OTPInvalidCode
        """

        phone = cls.normalize_phone(
            phone
        )

        purpose = cls.validate_purpose(
            purpose
        )

        code = str(code).strip()

        error = None
        verified_otp = None

        # =============================================
        # Atomic verification
        # =============================================

        with transaction.atomic():

            otp = (
                OTPCode.objects
                .select_for_update()
                .filter(
                    phone=phone,
                    purpose=purpose,
                    is_used=False,
                )
                .order_by("-created_at")
                .first()
            )

            # -----------------------------------------
            # No OTP
            # -----------------------------------------

            if otp is None:
                error = OTPNotFound(
                    "No active OTP was found."
                )

            # -----------------------------------------
            # Expired
            # -----------------------------------------

            elif otp.is_expired:

                otp.is_used = True

                otp.save(
                    update_fields=[
                        "is_used"
                    ]
                )

                error = OTPExpired(
                    "OTP has expired."
                )

            # -----------------------------------------
            # Max attempts already reached
            # -----------------------------------------

            elif otp.is_max_attempts_reached:

                otp.is_used = True

                otp.save(
                    update_fields=[
                        "is_used"
                    ]
                )

                error = OTPMaxAttemptsReached(
                    "Maximum OTP attempts reached."
                )

            # -----------------------------------------
            # Invalid code
            # -----------------------------------------

            elif not otp.check_code(code):

                otp.attempts += 1

                remaining_attempts = max(
                    otp.max_attempts
                    - otp.attempts,
                    0,
                )

                update_fields = [
                    "attempts"
                ]

                # This was the final allowed attempt.
                if (
                    otp.attempts
                    >= otp.max_attempts
                ):

                    otp.is_used = True

                    update_fields.append(
                        "is_used"
                    )

                    error = (
                        OTPMaxAttemptsReached(
                            "Maximum OTP attempts reached."
                        )
                    )

                else:

                    error = OTPInvalidCode(
                        remaining_attempts=(
                            remaining_attempts
                        )
                    )

                otp.save(
                    update_fields=update_fields
                )

            # -----------------------------------------
            # Success
            # -----------------------------------------

            else:

                otp.is_used = True

                otp.save(
                    update_fields=[
                        "is_used"
                    ]
                )

                verified_otp = otp

        # =============================================
        # IMPORTANT:
        #
        # Raise AFTER transaction.atomic.
        #
        # If we raised OTPInvalidCode inside the atomic
        # block, Django would rollback `attempts += 1`.
        # =============================================

        if error is not None:
            raise error

        return verified_otp