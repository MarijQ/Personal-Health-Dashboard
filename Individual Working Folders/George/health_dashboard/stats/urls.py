from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),  # Upload page
    path('dash_app/', views.dash_app_view, name='dash_app'),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),# Custom view for Dash integration
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
