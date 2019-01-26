from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomPasswordChangeView, ProfileView, RegisterView

app_name = 'accounts'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.logout_then_login, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password_change/', CustomPasswordChangeView.as_view(),
         name='password_change'),
]
