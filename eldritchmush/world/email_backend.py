"""
Django email backend that sends through the game's Resend setup
(world/email.py), so django-allauth's verification emails and any other
Django mail use the same sender and API key as the game's own email.

Settings: EMAIL_BACKEND = "world.email_backend.ResendEmailBackend".
Without RESEND_API_KEY, world.email logs the skip and nothing is sent.
"""
import html
import re

from django.core.mail.backends.base import BaseEmailBackend

_URL_RX = re.compile(r"(https?://[^\s<>\"]+)")


def text_to_html(text):
    """Plain text to simple HTML: escaped, paragraphs kept, links live."""
    paras = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    out = []
    for p in paras:
        esc = html.escape(p).replace("\n", "<br>")
        esc = _URL_RX.sub(r'<a href="\1">\1</a>', esc)
        out.append(f"<p>{esc}</p>")
    return ("<div style=\"font-family: Georgia, serif; max-width: 600px; "
            "margin: 0 auto;\">" + "".join(out) + "</div>")


class ResendEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        from world.email import send_email
        sent = 0
        for message in email_messages or []:
            html_body = None
            for content, mimetype in getattr(message, "alternatives", []) or []:
                if mimetype == "text/html":
                    html_body = content
            if getattr(message, "content_subtype", "plain") == "html":
                html_body, text_body = message.body, None
            else:
                text_body = message.body
            if html_body is None:
                html_body = text_to_html(text_body)
            recipients = list(message.to or []) + list(message.cc or []) \
                + list(message.bcc or [])
            if not recipients:
                continue
            ok = False
            try:
                ok = send_email(recipients, message.subject, html_body,
                                text_body=text_body)
            except Exception:
                if not self.fail_silently:
                    raise
            if ok:
                sent += 1
        return sent
