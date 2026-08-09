"""
URL configuration for helpdes project.

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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from tickets import views as ticket_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tickets.urls')),
    path('users/', include('users.urls')),
    path('company/', include('company.urls')),

    # Authentication URLs
    path('login/', ticket_views.CustomLoginView.as_view(template_name='tickets/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='tickets/auth/logout.html'), name='logout'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# Add static and media file handling in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# En producción los estáticos los sirve Whitenoise y media depende de storage (S3 si está configurado).

# Error handlers
handler404 = 'helpdesk.views.handler404'
handler500 = 'helpdesk.views.handler500'
handler400 = 'helpdesk.views.handler400'
