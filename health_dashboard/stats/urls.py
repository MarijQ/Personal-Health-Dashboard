from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-secret/', views.upload_secret, name='upload_secret'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('set-api-key/', views.set_api_key, name='set_api_key'),
    path('get-ai-response/', views.get_ai_response, name='get_ai_response'),

    # CSV and DB actions
    path('upload-csv-create-table/', views.upload_csv_create_table, name='upload_csv_create_table'),
    path('drop-all-tables/', views.drop_all_tables, name='drop_all_tables'),

    # Manual data
    path('add-manual-data/', views.add_manual_data, name='add_manual_data'),
    path('remove-last-manual-data/', views.remove_last_manual_data, name='remove_last_manual_data'),
]
