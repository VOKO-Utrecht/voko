from django.template import Template, Context
import html2text
from mailing.models import MailTemplate


def render_mail_template(template, **kwargs):
    body_tpl = Template(template.html_body)
    subject_tpl = Template(template.subject)
    context = Context(kwargs)

    rendered_subject = subject_tpl.render(context)
    rendered_html_body = body_tpl.render(context)

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    rendered_plain_body = h2t.handle(rendered_html_body)

    return rendered_subject, rendered_html_body, rendered_plain_body


def get_template_by_id(template_id):
    return MailTemplate.objects.get(id=template_id)