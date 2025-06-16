"""
URL configuration for smarttasker_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# project-level urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from tasks.views import (
    register_view,
    forgot_password_view,
    logout_view,
    reset_password_view,
    SafeTokenObtainPairView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/login/', SafeTokenObtainPairView.as_view(), name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ✅ Handles /api/tasks/ and /api/tasks/stats/
    path('api/', include('tasks.urls')),

    # Auth endpoints
    path('api/auth/register/', register_view, name='register'),
    path('api/auth/logout/', logout_view, name='logout'),
    path('api/auth/forgot-password/', forgot_password_view, name='forgot-password'),
    path('api/auth/reset-password/<uidb64>/<token>/', reset_password_view, name='reset-password'),
]
