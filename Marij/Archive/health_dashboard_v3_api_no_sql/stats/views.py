from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
import os
import time
import requests
import pandas as pd
from google_auth_oauthlib.flow import Flow

# Update with your scope
SCOPES = ["https://www.googleapis.com/auth/fitness.activity.read"]


def home(request):
    steps_data = request.session.pop("steps_data", None)
    return render(request, "stats/upload.html", {"steps_data": steps_data})


def upload_secret(request):
    print("upload_secret triggered")

    if request.method == "POST" and request.FILES.get("client_secret"):
        uploaded_file = request.FILES["client_secret"]

        # Ensure the tmp directory exists before saving the file
        tmp_dir = default_storage.path("tmp/")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
            print(f"Created directory: {tmp_dir}")

        temp_secret_path = os.path.join(tmp_dir, "client_secret.json")
        with open(temp_secret_path, "wb") as f:
            f.write(uploaded_file.read())
        print(f"File uploaded and saved to {temp_secret_path}")

        # Start the authorization flow
        try:
            flow = Flow.from_client_secrets_file(
                temp_secret_path,
                scopes=SCOPES,
                redirect_uri="http://localhost:8000/oauth2callback",  # Update this if running remotely
            )
            authorization_url, state = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )
            request.session["oauth_state"] = state
            print(f"Redirecting to authorization URL: {authorization_url}")

            request.session["temp_secret_path"] = temp_secret_path
            return redirect(authorization_url)
        except Exception as e:
            print(f"Error in upload_secret: {e}")
            if os.path.exists(temp_secret_path):
                os.remove(temp_secret_path)  # Cleanup if there's an error
            return JsonResponse({"error": str(e)}, status=400)

    print("No file uploaded or wrong HTTP method")
    return redirect("home")


def oauth2callback(request):
    print("oauth2callback triggered")
    temp_secret_path = request.session.pop("temp_secret_path", None)
    state = request.session.pop("oauth_state", None)

    if not temp_secret_path:
        print("Temporary client secret path not found")
        messages.error(request, "Temporary client secret file not found.")
        return redirect("home")

    try:
        flow = Flow.from_client_secrets_file(
            temp_secret_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/oauth2callback",
        )
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        print("Credentials successfully fetched")

        # Fetch steps data
        steps_data = fetch_steps_data(credentials)
        print(f"Steps data fetched to be displayed: {steps_data}")  # Debugging
        request.session["steps_data"] = steps_data or "<p>No data fetched</p>"
    except Exception as e:
        print(f"Error during OAuth callback: {e}")
        messages.error(request, f"Error during OAuth callback: {e}")
    finally:
        if os.path.exists(temp_secret_path):
            os.remove(temp_secret_path)

    return redirect("home")


def fetch_steps_data(credentials):
    """Fetch steps data from Google Fit API."""
    # Define specific date range
    start_time_str = "2024-11-01"
    end_time_str = "2024-11-14"

    # Convert to milliseconds since epoch
    start_time_millis = int(time.mktime(time.strptime(start_time_str, "%Y-%m-%d")) * 1000)
    end_time_millis = int(time.mktime(time.strptime(end_time_str, "%Y-%m-%d")) * 1000)

    url = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate'
    headers = {'Authorization': f'Bearer {credentials.token}'}
    body = {
        "aggregateBy": [{
            "dataTypeName": "com.google.step_count.delta",
            "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas"
        }],
        "bucketByTime": {"durationMillis": 86400000},  # Daily aggregation
        "startTimeMillis": start_time_millis,
        "endTimeMillis": end_time_millis
    }

    print(f"Requesting data from {start_time_str} to {end_time_str}...")
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        data = response.json()
        steps_list = []
        for bucket in data.get('bucket', []):
            start_time = int(bucket['startTimeMillis']) // 1000
            date = time.strftime('%Y-%m-%d', time.gmtime(start_time))
            steps = sum(
                point['value'][0]['intVal']
                for dataset in bucket.get('dataset', [])
                for point in dataset.get('point', [])
            )
            steps_list.append({'date': date, 'steps': steps})

        df = pd.DataFrame(steps_list)
        print(f"Steps data processed: {steps_list}")  # Debugging
        return df.to_html(index=False)
    else:
        print(f"Google Fit API error: {response.status_code} - {response.text}")
        return f"<p>Error fetching data: {response.status_code} - {response.text}</p>"
