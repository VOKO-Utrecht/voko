from django.urls import path
from mailing.views import PreviewMailView, ChooseTemplateView, SendMailView

urlpatterns = (
    path('sendmail/',
         ChooseTemplateView.as_view(),
         name="admin_choose_mail_template"),
    path('sendmail/preview/<pk>/',
         PreviewMailView.as_view(),
         name="admin_preview_mail"),
    path('sendmail/send/<pk>/',
         SendMailView.as_view(),
         name="admin_send_mail"),
)
