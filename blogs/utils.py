from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, recipient_list, context, text_message):

    html_content = render_to_string(
        'base_email.html',
        context
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )

    email.attach_alternative(html_content, "text/html")

    email.send()
