from braces.views import StaffuserRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse, StreamingHttpResponse
from django.template import Template, Context
from django.views.generic import TemplateView, ListView, View
from accounts.models import VokoUser
from mailing.models import MailTemplate
from ordering.core import get_current_order_round
import html2text


def _render_template(template, user, order_round):
    body_tpl = Template(template.html_body)
    subject_tpl = Template(template.subject)
    context = Context({'user': user, 'order_round': order_round})

    rendered_subject = subject_tpl.render(context)
    rendered_html_body = body_tpl.render(context)

    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    rendered_plain_body = h2t.handle(rendered_html_body)

    return rendered_subject, rendered_html_body, rendered_plain_body


class ChooseTemplateView(StaffuserRequiredMixin, ListView):
    model = MailTemplate
    template_name = "mailing/admin/mailtemplate_list.html"


class PreviewMailView(StaffuserRequiredMixin, TemplateView):
    template_name = "mailing/admin/preview_mail.html"

    def get_context_data(self, **kwargs):
        context = super(PreviewMailView, self).get_context_data(**kwargs)

        users = [VokoUser.objects.get(pk=uid) for uid in self.request.session.get('mailing_user_ids')]
        context['mailing_users'] = users

        template = MailTemplate.objects.get(pk=self.kwargs.get('pk'))
        context['template'] = template

        context['example'] = _render_template(template, self.request.user, get_current_order_round())

        return context


class SendMailView(StaffuserRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        self.users = [VokoUser.objects.get(pk=uid) for uid in self.request.session.get('mailing_user_ids')]
        self.template = MailTemplate.objects.get(pk=self.kwargs.get('pk'))
        self.current_order_round = get_current_order_round()

        # TODO: Clear users from session. Below code doesn't work
        # request.session['mailing_user_ids'] = []
        # del request.session['mailing_user_ids']

        self._send_mails()

        return HttpResponse("Klaar! <a href='/admin'>Klik</a>")

    def _send_mails(self):
        for user in self.users:
            subject, html_message, plain_message = _render_template(self.template, user, self.current_order_round)

            send_mail(subject=subject,
                      message=plain_message,
                      from_email="VOKO Utrecht <info@vokoutrecht.nl>",
                      recipient_list=[user.email],
                      html_message=html_message)


