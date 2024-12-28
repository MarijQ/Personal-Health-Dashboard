from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-secret/', views.upload_secret, name='upload_secret'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('set-api-key/', views.set_api_key, name='set_api_key'),
    path('get-ai-response/', views.get_ai_response, name='get_ai_response'),
]
