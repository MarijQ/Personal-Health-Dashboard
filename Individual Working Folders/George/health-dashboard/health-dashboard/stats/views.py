from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Avg, StdDev 
from .models import BloodPressure
import pandas as pd
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import time


def csv_load(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            return render(request, 'stats/upload.html', {'error': 'This is not a CSV file.'})

        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)

        # Read the CSV file into a Pandas DataFrame
        try:
            df = pd.read_csv(file_path)
            
             # Check if the DataFrame is empty
            if df.empty:
                return render(request, 'stats/upload.html', {'error': 'The CSV file is empty.'})
            else:      
                for _, row in df.iterrows():   
                    BloodPressure.objects.create(
                        blood_pressure = row['Blood Pressure']
                    )
        except Exception as e:
            return render(request, 'stats/upload.html', {'error': f'Error reading CSV file: {e}'})

        fs.delete(filename)  # Clean up the uploaded file
        
        return redirect(csv_process)
    
    return render(request, 'stats/upload.html')


def csv_process(request): 
        
        aggregated_data = BloodPressure.objects.aggregate(
            avg_blood_pressure = Avg('blood_pressure'),
            std_blood_pressure = StdDev('blood_pressure')
        )

        # Prepare the data for display
        formatted_data = ({
            'header': 'Blood Pressure Metrics',
            'mean': aggregated_data['avg_blood_pressure'],
            'standard_deviation': f"{aggregated_data['std_blood_pressure']:.2f}"
        })

        return render(request, 'stats/upload.html', {'numerical_data': formatted_data})



def google_fit_authorize(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(r'C:\Users\ggeor\Desktop\health_dashboard\health_dashboard\client_secret_335499598454-hdfm9l67a8cthpr0c5hin8pbb7fdtb1t.apps.googleusercontent.com.json'),
        scopes=['https://www.googleapis.com/auth/fitness.activity.read'],
        redirect_uri='http://localhost:8000/fit/callback'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)


def google_fit_callback(request):
    flow = Flow.from_client_secrets_file(
        os.path.join(r'C:\Users\ggeor\Desktop\health_dashboard\health_dashboard\client_secret_335499598454-hdfm9l67a8cthpr0c5hin8pbb7fdtb1t.apps.googleusercontent.com.json'),
        scopes=['https://www.googleapis.com/auth/fitness.activity.read'],
        redirect_uri='http://localhost:8000/fit/callback'
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    request.session['google_fit_credentials'] = credentials_to_dict(credentials)
    
    print("Stored Google Fit Credentials:", request.session.get('google_fit_credentials'))
    return redirect('/fit/data')


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    

def get_fit_data(request):
    if 'google_fit_credentials' not in request.session:
        return redirect('/fit/authorize')
    
    creds = Credentials(**request.session['google_fit_credentials'])
    service = build('fitness', 'v1', credentials=creds)
    
    # Define time range for the dataset ID 
    end_time_ns = int(time.time() * 1e9)  # Current time in nanoseconds
    start_time_ns = int((time.time() - 86400) * 1e9)  # 24 hours ago in nanoseconds
    
    dataset_id = f"{start_time_ns}-{end_time_ns}"
    # steps count 
    response = service.users().dataSources().datasets().get(
        userId='me',
        dataSourceId='derived:com.google.step_count.delta:com.google.android.gms:estimated_steps',
        datasetId=dataset_id
    ).execute()
    
    print("Google Fit API Response:", response)

    steps = response.get('point', [])
    return render(request, 'fit_data.html', {'steps': steps})
