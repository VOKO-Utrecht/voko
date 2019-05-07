from django.conf import settings
import log
from django.core.mail import send_mail
from django.template import Template, Context
import html2text
from mailing.models import MailTemplate


def render_mail_template(template, **kwargs):
    body_tpl = Template(template.html_body)
    subject_tpl = Template(template.subject)
    from_email_tpl = Template(template.from_email)
    context = Context(kwargs)

    rendered_subject = subject_tpl.render(context)
    rendered_from_email = from_email_tpl.render(context)
    rendered_html_body = body_tpl.render(context)

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    rendered_plain_body = h2t.handle(rendered_html_body)

    return (
        rendered_subject,
        rendered_html_body,
        rendered_plain_body,
        rendered_from_email
    )


def get_template_by_id(template_id):
    try:
        return MailTemplate.objects.get(id=template_id)
    except MailTemplate.DoesNotExist:
        if settings.DEBUG:
            return MailTemplate(title="TEST")


def mail_user(user, subject, html_body, plain_body, from_email):
    default_from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject=subject,
              message=plain_body,
              from_email=from_email if from_email else default_from_email,
              recipient_list=["%s <%s>" % (user.get_full_name(), user.email)],
              html_message=html_body)
    log.log_event(user=user, event="Mail sent: %s" % subject, extra=html_body)
