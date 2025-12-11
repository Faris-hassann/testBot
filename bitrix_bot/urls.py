"""
URL configuration for bitrix_bot project.
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import RedirectView
from bot import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger/OpenAPI schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Bitrix24 Bot API",
        default_version='v1',
        description="API documentation for Bitrix24 Bot - Send and Receive Messages",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@bitrixbot.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Redirect root to Swagger
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='root'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Swagger/OpenAPI documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints - Bot event handlers
    path('bot/message', views.bot_message, name='bot_message'),
    path('bot/welcome', views.bot_welcome, name='bot_welcome'),
    path('bot/delete', views.bot_delete, name='bot_delete'),
    
    # Legacy endpoint (for backward compatibility)
    path('b24-hook.php', views.bot_message, name='webhook'),
]

