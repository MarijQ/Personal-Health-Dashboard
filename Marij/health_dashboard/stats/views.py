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

# Constants
SCOPES = ["https://www.googleapis.com/auth/fitness.activity.read"]
API_KEY_FILE = os.path.join(settings.MEDIA_ROOT, "api_key.txt")
SITE_URL = "http://localhost:8000"
APP_NAME = "Health Dashboard"

# ----------------------------------------------------------------------
# General Views
# ----------------------------------------------------------------------


def home(request):
    """
    Handles the homepage view where user-specific steps data is retrieved
    and optionally displayed in a table format.
    """
    user_id = request.session.session_key or "anonymous_user"
    steps_data = UserSteps.objects.filter(user_id=user_id).order_by("date")

    # Convert data to a dataframe and optionally render as an HTML table
    steps_df = pd.DataFrame(list(steps_data.values("date", "steps")))
    steps_table = steps_df.to_html(index=False) if not steps_df.empty else None

    return render(request, "stats/upload.html", {"steps_data": steps_table})


# ----------------------------------------------------------------------
# Google Fit Integration
# ----------------------------------------------------------------------


def upload_secret(request):
    """
    Handles the upload of the `client_secret.json` file to initiate
    the Google Fit OAuth flow.
    """
    if request.method == "POST" and request.FILES.get("client_secret"):
        uploaded_file = request.FILES["client_secret"]

        # Ensure temporary directory exists and save file
        tmp_dir = default_storage.path("tmp/")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        temp_secret_path = os.path.join(tmp_dir, "client_secret.json")
        with open(temp_secret_path, "wb") as f:
            f.write(uploaded_file.read())

        # Start the authorization flow
        try:
            flow = Flow.from_client_secrets_file(
                temp_secret_path,
                scopes=SCOPES,
                redirect_uri="http://localhost:8000/oauth2callback",
            )
            authorization_url, state = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )
            request.session["oauth_state"] = state
            request.session["temp_secret_path"] = temp_secret_path

            return redirect(authorization_url)
        except Exception as e:
            if os.path.exists(temp_secret_path):
                os.remove(temp_secret_path)  # Clean-up on error
            return JsonResponse({"error": str(e)}, status=400)

    return redirect("home")


def oauth2callback(request):
    """
    Handles the OAuth2 callback from Google Fit after user authorization.
    Fetches steps data and stores it in the database.
    """
    temp_secret_path = request.session.pop("temp_secret_path", None)
    state = request.session.pop("oauth_state", None)

    if not temp_secret_path:
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

        # Fetch steps data and save to database
        user_id = request.session.session_key or "anonymous_user"
        fetch_steps_data(credentials, user_id)
        messages.success(request, "Steps data fetched and saved successfully!")
    except Exception as e:
        messages.error(request, f"Error during OAuth callback: {e}")
    finally:
        if os.path.exists(temp_secret_path):
            os.remove(temp_secret_path)

    return redirect("home")


def fetch_steps_data(credentials, user_id):
    """
    Fetches steps data from the Google Fit API and saves it to the database,
    avoiding duplicate entries.
    """
    start_time_str = "2024-11-01"
    end_time_str = "2024-11-16"

    # Convert start and end times to milliseconds since epoch
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
        )

        for bucket in data.get("bucket", []):
            start_time = int(bucket["startTimeMillis"]) // 1000
            date = time.strftime("%Y-%m-%d", time.gmtime(start_time))
            steps = sum(
                point["value"][0]["intVal"]
                for dataset in bucket.get("dataset", [])
                for point in dataset.get("point", [])
            )
            if date not in existing_dates:
                steps_to_create.append(
                    UserSteps(user_id=user_id, date=date, steps=steps)
                )

        UserSteps.objects.bulk_create(steps_to_create, ignore_conflicts=True)
    else:
        raise Exception(
            f"Error fetching data: {response.status_code} - {response.text}"
        )


# ----------------------------------------------------------------------
# AI Integration (OpenRouter)
# ----------------------------------------------------------------------


def set_api_key(request):
    """
    Saves the user's OpenRouter API key.
    """
    if request.method == "POST":
        api_key = request.POST.get("api_key", "").strip()
        if not api_key:
            messages.error(request, "API key cannot be empty.")
            return redirect("home")

        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        messages.success(request, "API key saved successfully.")
        return redirect("home")
    return redirect("home")


def get_stored_api_key():
    """
    Retrieves the stored OpenRouter API key from a file if available.
    """
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return None


def get_ai_response(request):
    """
    Generates an AI response using OpenRouter's API based on user input
    and context retrieved from the database.
    """
    if request.method == "POST":
        api_key = get_stored_api_key()
        if not api_key:
            return JsonResponse(
                {"error": "No API key configured. Please set an API key first."},
                status=400,
            )

        try:
            body = json.loads(request.body)
            prompt = body.get("prompt", "").strip()
            if not prompt:
                return JsonResponse({"error": "Prompt is missing."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON input."}, status=400)

        # Fetch context data for AI interaction
        sqlite_data = fetch_steps_context()
        full_prompt = f"User Question: {prompt}\n\nUser Data:\n{sqlite_data}"

        # Send request to OpenRouter
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": SITE_URL,
                "X-Title": APP_NAME,
            }
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": full_prompt}],
            }
            response = requests.post(
                openrouter_url, headers=headers, data=json.dumps(payload)
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = (
                    data.get("choices", [])[0]
                    .get("message", {})
                    .get("content", "No response received.")
                )
                return JsonResponse({"response": ai_response})
            else:
                return JsonResponse(
                    {"error": f"OpenRouter error: {response.text}"},
                    status=response.status_code,
                )
        except Exception as e:
            return JsonResponse(
                {"error": f"Could not connect to OpenRouter: {str(e)}"}, status=500
            )


def fetch_steps_context():
    """
    Extracts formatted steps data from the database for use in prompt generation.
    """
    steps = UserSteps.objects.all().order_by("user_id", "date")
    context = [f"{step.user_id} - {step.date}: {step.steps} steps" for step in steps]
    return "\n".join(context)
