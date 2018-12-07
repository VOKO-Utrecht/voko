from django.conf.urls import url
from mailing.views import PreviewMailView, ChooseTemplateView, SendMailView

urlpatterns = (
    url(r'^sendmail/$',
        ChooseTemplateView.as_view(),
        name="admin_choose_mail_template"),
    url(r'^sendmail/preview/(?P<pk>[0-9]+)/$',
        PreviewMailView.as_view(),
        name="admin_preview_mail"),
    url(r'^sendmail/send/(?P<pk>[0-9]+)/$',
        SendMailView.as_view(),
        name="admin_send_mail"),
  )
