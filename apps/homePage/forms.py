from allauth.account.forms import ResetPasswordForm
from allauth.account.adapter import get_adapter


class QRResetPasswordForm(ResetPasswordForm):
    """Capture the generated reset URL so we can show a QR on the confirmation page."""

    def save(self, request, **kwargs):
        adapter = get_adapter(request)
        captured: dict[str, str] = {}
        original_send_mail = adapter.send_mail

        def capture_send_mail(template_prefix, email, context):
            captured["password_reset_url"] = context.get("password_reset_url")
            return original_send_mail(template_prefix, email, context)

        adapter.send_mail = capture_send_mail
        try:
            response = super().save(request, **kwargs)
        finally:
            adapter.send_mail = original_send_mail

        # Stash the reset URL in the session for the success page QR display.
        url = captured.get("password_reset_url")
        if url:
            request.session["last_password_reset_url"] = url
            request.session.modified = True
        return response
