import logging
from smtplib import SMTPException
import threading

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

log = logging.getLogger(__name__)


class AutoConnectSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Automatically attach a social login to an existing account that shares the
    same verified email. This prevents the "user with this email already
    exists" error when a guest signs in with Google just to fetch a receipt.
    """

    def _extract_email(self, sociallogin) -> str | None:
        """Best-effort email extraction from the social login payload."""
        email = (sociallogin.user and sociallogin.user.email) or None
        if email:
            return email
        # Prefer verified emails provided by the provider
        for address in sociallogin.email_addresses:
            if address.email:
                return address.email
        return sociallogin.account.extra_data.get("email")

    def pre_social_login(self, request, sociallogin):
        # If this social account is already linked, let allauth proceed.
        if sociallogin.is_existing:
            return

        email = self._extract_email(sociallogin)
        if not email:
            return

        # Only auto-connect when the provider told us the email is verified
        is_verified = any(addr.verified for addr in sociallogin.email_addresses)
        if sociallogin.account.extra_data.get("email_verified") is True:
            is_verified = True
        if not is_verified:
            return

        User = get_user_model()
        try:
            existing_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # Guard against cross-linking to the wrong user if something is off.
        if sociallogin.account.user_id and sociallogin.account.user_id != existing_user.id:
            return

        sociallogin.connect(request, existing_user)


class SafeAccountAdapter(DefaultAccountAdapter):
    """
    Make password-reset and signup emails fail-safe: if SMTP rejects the send
    (e.g., Gmail auth/app password issues), log the error and fallback to the
    console backend instead of returning HTTP 500.

    Also offload sending to a background thread so the HTTP response is fast
    even if SMTP is slow.
    """

    def send_mail(self, template_prefix, email, context):
        def _send():
            try:
                super(SafeAccountAdapter, self).send_mail(template_prefix, email, context)
            except SMTPException as exc:
                log.warning("Primary email send failed, falling back to console backend: %s", exc)
                try:
                    message = self.render_mail(template_prefix, email, context)
                    message.connection = self.get_email_backend("django.core.mail.backends.console.EmailBackend")
                    message.send()
                except Exception as console_exc:
                    log.error("Console email fallback also failed: %s", console_exc)
            except Exception as exc:
                log.error("Unexpected error sending mail: %s", exc)

        threading.Thread(target=_send, daemon=True).start()
        # return immediately; background thread handles send
        return None

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Allauth normally sends confirmation synchronously during signup.
        Offload to background thread to avoid blocking the signup response.
        """
        def _send():
            try:
                super(SafeAccountAdapter, self).send_confirmation_mail(request, emailconfirmation, signup)
            except SMTPException as exc:
                log.warning("Signup confirmation send failed: %s", exc)
                try:
                    message = self.render_mail(
                        "account/email/email_confirmation",
                        emailconfirmation.email_address.email,
                        {"email": emailconfirmation.email_address.email, "key": emailconfirmation.key},
                    )
                    message.connection = self.get_email_backend("django.core.mail.backends.console.EmailBackend")
                    message.send()
                except Exception as console_exc:
                    log.error("Console fallback for signup confirmation failed: %s", console_exc)
            except Exception as exc:
                log.error("Unexpected error sending confirmation mail: %s", exc)

        threading.Thread(target=_send, daemon=True).start()
        return None

    def get_login_redirect_url(self, request):
        """
        If a kiosk email-receipt flow provided a return URL, honor it once and
        then clear it. Otherwise, defer to the default behavior.
        """
        next_url = self.get_next_redirect_url(request)
        if next_url:
            return next_url
        receipt_return = request.session.pop("receipt_return_to", None)
        if receipt_return:
            # After login/signup for email receipt, go straight to the return target
            return receipt_return
        # If the kiosk email flow is active, force users back to order confirmation to send the receipt.
        if request.session.get("send_receipt_email") and request.session.get("last_order_id"):
            order_id = request.session.get("last_order_id")
            return f"/kiosk/order-confirmation/?order_id={order_id}"
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        """Mirror login redirect logic for signups."""
        next_url = self.get_next_redirect_url(request)
        if next_url:
            return next_url
        receipt_return = request.session.pop("receipt_return_to", None)
        if receipt_return:
            return receipt_return
        if request.session.get("send_receipt_email") and request.session.get("last_order_id"):
            order_id = request.session.get("last_order_id")
            return f"/kiosk/order-confirmation/?order_id={order_id}"
        return super().get_signup_redirect_url(request)
