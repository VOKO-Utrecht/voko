from django.urls import path
from accounts import views

urlpatterns = (
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),

    path('register/', views.RegisterView.as_view(), name="register"),
    path('register/thanks/',
         views.RegisterThanksView.as_view(),
         name="register_thanks"),
    path('register/confirm/<pk>/',
         views.EmailConfirmView.as_view(),
         name="confirm_email"),
    path('register/finish/<pk>/',
         views.FinishRegistration.as_view(),
         name="finish_registration"),

    path('passwordreset/',
         views.RequestPasswordResetView.as_view(),
         name="password_reset"),
    path('passwordreset/done/',
         views.PasswordResetRequestDoneView.as_view()),
    path('passwordreset/finished/',
         views.PasswordResetFinishedView.as_view()),
    path('passwordreset/reset/<pk>/',
         views.PasswordResetView.as_view(),
         name="reset_pass"),

    path('welcome/', views.WelcomeView.as_view()),
    path('overview/', views.OverView.as_view(), name='overview'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('updateProfile/', views.EditProfileView.as_view(), name='update_profile'),
    path('contact/', views.Contact.as_view(), name='contact'),
    path('orderHistory/', views.OrderHistory.as_view(), name='order_history'),

    path('profile/remarks/<pk>', views.EditCoordinatorRemarksView.as_view(),
         name='coordinator_remarks')
)
