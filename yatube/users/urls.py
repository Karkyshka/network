from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.urls import path

from . import views

app_name = 'users'


urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('password-reset/',
         PasswordResetView.as_view
         (template_name='users/password_reset_form.html'),
         name='password_reset_form'),
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path('login/', LoginView.as_view(template_name='users/login.html'),
         name='login'),
    path('password_change/',
         LoginView.as_view(template_name='users/password_change.html'),
         name='password_change'),
    path('done/',
         LoginView.as_view(template_name='users/password_change/done.html'),
         name='done'),
]
