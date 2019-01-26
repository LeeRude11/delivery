from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomPasswordChangeView, ProfileView

app_name = 'accounts'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('password_change/', CustomPasswordChangeView.as_view(),
         name='password_change'),
    path('profile/', ProfileView.as_view(), name='profile')
]
