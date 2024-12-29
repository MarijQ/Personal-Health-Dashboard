from django.urls import path
from . import views

urlpatterns = [
    path('', views.csv_load, name='csv_load'),
    path('process/', views.csv_process, name='csv_process'),
    path('fit/authorize', views.google_fit_authorize, name='google_fit_authorize'),
    path('fit/callback', views.google_fit_callback, name='google_fit_callback'),
    path('fit/data', views.get_fit_data, name='get_fit_data'),
]
