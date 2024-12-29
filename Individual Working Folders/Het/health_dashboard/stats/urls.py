from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Upload page
    path('dash_app/', include('django_plotly_dash.urls')),  # Include Django Plotly Dash URLs
    path('dash_app/', views.dash_app_view, name='dash_app'),  # Your custom view
]