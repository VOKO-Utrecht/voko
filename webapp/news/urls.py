from django.conf.urls import url
from news import views

urlpatterns = (
    url(r'^$', views.NewsitemsView.as_view(),
        name="view_newsitems"),
        url(r'^(?P<pk>[0-9]+)/$', views.NewsitemDetail.as_view(),
        name="view_newsitem"),
)
