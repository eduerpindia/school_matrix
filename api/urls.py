from django.urls import path, include
from .auth_views import LoginAPIView, RefreshTokenAPIView, LogoutAPIView

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/refresh/', RefreshTokenAPIView.as_view(), name='refresh_token'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('classes/', include('classes.urls')),
    path('teachers/', include('teachers.urls')),
    path('students/', include('students.urls')),
]