from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),  # Upload page
    path('dash_app/', views.dash_app_view, name='dash_app'),  # Dash app page
]
