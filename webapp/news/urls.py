from django.urls import path
from news import views

urlpatterns = (
    path('',
         views.NewsitemsView.as_view(),
         name="view_newsitems"),
    path('<pk>/',
         views.NewsitemsView.as_view(),
         name="view_newsitem"),
)
