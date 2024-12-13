from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from google_auth_oauthlib.flow import Flow
from .models import UserSteps
import os
import time
import requests
import pandas as pd
import json
import sqlite3

SCOPES = ["https://www.googleapis.com/auth/fitness.activity.read"]
API_KEY_FILE = os.path.join(settings.MEDIA_ROOT, "api_key.txt")
YOUR_SITE_URL = "http://localhost:8000"  # Replace with your app's deployed URL during production
YOUR_APP_NAME = "Health Dashboard"       # Change to the name of your app

def home(request):
    user_id = request.session.session_key or "anonymous_user"
    steps_data = UserSteps.objects.filter(user_id=user_id).order_by(
        "date"
    )  # Query data from DB

    # Convert queried data to HTML table (optional, for displaying in template)
    steps_df = pd.DataFrame(list(steps_data.values("date", "steps")))
    steps_table = steps_df.to_html(index=False) if not steps_df.empty else None

    return render(request, "stats/upload.html", {"steps_data": steps_table})


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

        # Use a session/user-specific ID for this example
        user_id = request.session.session_key or "anonymous_user"

        # Fetch and save steps data into the database
        fetch_steps_data(credentials, user_id)
        print("Steps data saved to database")
        messages.success(request, "Steps data fetched and saved successfully!")
    except Exception as e:
        print(f"Error during OAuth callback: {e}")
        messages.error(request, f"Error during OAuth callback: {e}")
    finally:
        if os.path.exists(temp_secret_path):
            os.remove(temp_secret_path)

    return redirect("home")


def fetch_steps_data(credentials, user_id):
    """Fetch steps data from Google Fit API and save unique entries to the database."""
    start_time_str = "2024-11-01"
    end_time_str = "2024-11-16"

    # Convert to milliseconds since epoch
    start_time_millis = int(
        time.mktime(time.strptime(start_time_str, "%Y-%m-%d")) * 1000
    )
    end_time_millis = int(time.mktime(time.strptime(end_time_str, "%Y-%m-%d")) * 1000)

    url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
    headers = {"Authorization": f"Bearer {credentials.token}"}
    body = {
        "aggregateBy": [
            {
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas",
            }
        ],
        "bucketByTime": {"durationMillis": 86400000},  # Daily aggregation
        "startTimeMillis": start_time_millis,
        "endTimeMillis": end_time_millis,
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        data = response.json()
        steps_to_create = []
        existing_dates = set(
            UserSteps.objects.filter(user_id=user_id).values_list("date", flat=True)
        )  # Get all existing dates for this user

        for bucket in data.get("bucket", []):
            start_time = int(bucket["startTimeMillis"]) // 1000
            date = time.strftime("%Y-%m-%d", time.gmtime(start_time))
            steps = sum(
                point["value"][0]["intVal"]
                for dataset in bucket.get("dataset", [])
                for point in dataset.get("point", [])
            )
            # Only add to list if date doesn't already exist in the database
            if date not in existing_dates:
                steps_to_create.append(
                    UserSteps(user_id=user_id, date=date, steps=steps)
                )

        # Bulk insert non-duplicate entries
        UserSteps.objects.bulk_create(steps_to_create, ignore_conflicts=True)
        print(f"Steps successfully saved for user: {user_id}")
    else:
        print(f"Google Fit API error: {response.status_code} - {response.text}")
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )


def set_api_key(request):
    """Save the user's OpenRouter API key."""
    if request.method == "POST":
        api_key = request.POST.get("api_key", "").strip()
        if not api_key:
            messages.error(request, "API key cannot be empty.")
            return redirect("home")
        # Save the key to a plaintext file
        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        messages.success(request, "API key saved successfully.")
        return redirect("home")
    return redirect("home")

def get_stored_api_key():
    """Retrieve the stored API key (if available)."""
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return None

def get_ai_response(request):
    """Generate AI response via OpenRouter."""
    if request.method == "POST":
        api_key = get_stored_api_key()
        if not api_key:
            return JsonResponse({"error": "No API key configured. Please set an API key first."}, status=400)

        # Parse the user prompt
        try:
            body = json.loads(request.body)
            prompt = body.get("prompt", "").strip()
            if not prompt:
                return JsonResponse({"error": "Prompt is missing."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON input."}, status=400)

        # Fetch additional context from SQLite (steps data in this example)
        sqlite_data = fetch_steps_context()

        # Combine the prompt with SQLite data
        full_prompt = f"User Question: {prompt}\n\nUser Data:\n{sqlite_data}"

        # Send the data to OpenRouter
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_APP_NAME,
            }
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": "openai/gpt-3.5-turbo",  # Optional: Adjust model as required
                "messages": [
                    {"role": "user", "content": full_prompt}
                ],
            }
            response = requests.post(openrouter_url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("choices", [])[0].get("message", {}).get("content", "No response received.")
                return JsonResponse({"response": ai_response})
            else:
                return JsonResponse({"error": f"OpenRouter error: {response.text}"}, status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": f"Could not connect to OpenRouter: {str(e)}"}, status=500)

def fetch_steps_context():
    """Extract steps data from SQLite database to include in the prompt."""
    steps = UserSteps.objects.all().order_by("user_id", "date")
    context = []
    for step in steps:
        context.append(f"{step.user_id} - {step.date}: {step.steps} steps")
    return "\n".join(context)