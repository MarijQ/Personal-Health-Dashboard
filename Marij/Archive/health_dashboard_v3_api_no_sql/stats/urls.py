from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-secret/', views.upload_secret, name='upload_secret'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
]
