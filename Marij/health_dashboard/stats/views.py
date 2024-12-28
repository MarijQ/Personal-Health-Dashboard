from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from google_auth_oauthlib.flow import Flow
from django.db.utils import OperationalError
from .models import UserSteps, ManualData, UserHR, UserCalories, UserSleep
import os
import time
import requests
import pandas as pd
import json
import csv
import sqlite3
import datetime

# Constants
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.sleep.read"
]
API_KEY_FILE = os.path.join(settings.MEDIA_ROOT, "api_key.txt")
SITE_URL = "http://localhost:8000"
APP_NAME = "Health Dashboard"


def home(request):
    """
    Home view renders the main dashboard.
    If essential tables are missing, handles the error gracefully.
    """
    try:
        user_id = request.session.session_key or "anonymous_user"
        steps_data = UserSteps.objects.filter(user_id=user_id).order_by("date")
        steps_df = pd.DataFrame(list(steps_data.values("date", "steps")))
        steps_table = steps_df.to_html(index=False) if not steps_df.empty else None
    except OperationalError as e:
        steps_table = None
        messages.error(request, f"Essential table is missing: {e}. Please recreate the database.")

    # List all tables and row counts (excluding system/core tables)
    table_info = list_tables_and_counts()

    # Fetch the last 10 manual entries (newest first)
    last_10_manual_data = ManualData.objects.order_by('-id')[:10]

    return render(request, "stats/dashboard.html", {
        "steps_data": steps_table,  # still available if we ever need it
        "table_info": table_info,
        "last_10_manual_data": last_10_manual_data,
    })


def upload_secret(request):
    if request.method == "POST" and request.FILES.get("client_secret"):
        uploaded_file = request.FILES["client_secret"]
        tmp_dir = default_storage.path("tmp/")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        temp_secret_path = os.path.join(tmp_dir, "client_secret.json")
        with open(temp_secret_path, "wb") as f:
            f.write(uploaded_file.read())

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
                os.remove(temp_secret_path)
            return JsonResponse({"error": str(e)}, status=400)

    return redirect("home")


def oauth2callback(request):
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

        user_id = request.session.session_key or "anonymous_user"
        fetch_all_fit_data(credentials, user_id)
        messages.success(request, "Data fetched (steps, HR, calories, sleep) and saved successfully!")
    except Exception as e:
        messages.error(request, f"Error during OAuth callback: {e}")
    finally:
        if os.path.exists(temp_secret_path):
            os.remove(temp_secret_path)

    return redirect("home")


def fetch_all_fit_data(credentials, user_id):
    """
    Fetch Steps, HR, Calories, and Sleep from Google Fit in daily buckets
    for a hard-coded date range. Extend or modify as needed.
    """
    start_time_str = "2024-11-01"
    end_time_str = "2024-11-16"

    start_time_millis = int(time.mktime(time.strptime(start_time_str, "%Y-%m-%d")) * 1000)
    end_time_millis = int(time.mktime(time.strptime(end_time_str, "%Y-%m-%d")) * 1000)

    def aggregate_fitness_data(data_type_name, data_source_id):
        url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"
        headers = {"Authorization": f"Bearer {credentials.token}"}
        body = {
            "aggregateBy": [
                {
                    "dataTypeName": data_type_name,
                    "dataSourceId": data_source_id,
                }
            ],
            "bucketByTime": {"durationMillis": 86400000},  # 1 day
            "startTimeMillis": start_time_millis,
            "endTimeMillis": end_time_millis,
        }
        response = requests.post(url, headers=headers, json=body)
        if response.status_code != 200:
            raise Exception(f"Error fetching {data_type_name}: {response.status_code} - {response.text}")
        return response.json()

    # 1) Steps
    steps_data = aggregate_fitness_data(
        "com.google.step_count.delta",
        "derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas"
    )
    existing_step_dates = set(
        UserSteps.objects.filter(user_id=user_id).values_list("date", flat=True)
    )
    steps_to_create = []
    for bucket in steps_data.get("bucket", []):
        start_time = int(bucket["startTimeMillis"]) // 1000
        date = time.strftime("%Y-%m-%d", time.gmtime(start_time))
        steps = sum(
            point["value"][0]["intVal"]
            for dataset in bucket.get("dataset", [])
            for point in dataset.get("point", [])
        )
        if date not in existing_step_dates:
            steps_to_create.append(UserSteps(user_id=user_id, date=date, steps=steps))
    UserSteps.objects.bulk_create(steps_to_create, ignore_conflicts=True)

    # 2) Heart Rate
    hr_data = aggregate_fitness_data(
        "com.google.heart_rate.bpm",
        "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
    )
    existing_hr_dates = set(
        UserHR.objects.filter(user_id=user_id).values_list("date", flat=True)
    )
    hr_to_create = []
    for bucket in hr_data.get("bucket", []):
        start_time = int(bucket["startTimeMillis"]) // 1000
        date = time.strftime("%Y-%m-%d", time.gmtime(start_time))

        hr_values = []
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                hr_values.append(point["value"][0]["fpVal"])
        if hr_values:
            avg_hr = sum(hr_values) / len(hr_values)
        else:
            avg_hr = 0.0

        if date not in existing_hr_dates:
            hr_to_create.append(UserHR(user_id=user_id, date=date, average_hr=avg_hr))
    UserHR.objects.bulk_create(hr_to_create, ignore_conflicts=True)

    # 3) Calories
    cal_data = aggregate_fitness_data(
        "com.google.calories.expended",
        "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended"
    )
    existing_cal_dates = set(
        UserCalories.objects.filter(user_id=user_id).values_list("date", flat=True)
    )
    cal_to_create = []
    for bucket in cal_data.get("bucket", []):
        start_time = int(bucket["startTimeMillis"]) // 1000
        date = time.strftime("%Y-%m-%d", time.gmtime(start_time))

        total_cal = 0.0
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                total_cal += point["value"][0]["fpVal"]
        if date not in existing_cal_dates:
            cal_to_create.append(UserCalories(user_id=user_id, date=date, calories=total_cal))
    UserCalories.objects.bulk_create(cal_to_create, ignore_conflicts=True)

    # 4) Sleep
    sleep_data = aggregate_fitness_data(
        "com.google.sleep.segment",
        "derived:com.google.sleep.segment:com.google.android.gms:merged"
    )
    existing_sleep_dates = set(
        UserSleep.objects.filter(user_id=user_id).values_list("date", flat=True)
    )
    sleep_to_create = []
    for bucket in sleep_data.get("bucket", []):
        start_time = int(bucket["startTimeMillis"]) // 1000
        date = time.strftime("%Y-%m-%d", time.gmtime(start_time))
        total_sleep_mins = 0

        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                seg_start = point["startTimeNanos"]
                seg_end = point["endTimeNanos"]
                duration_sec = (int(seg_end) - int(seg_start)) / 1e9
                # Real logic might skip awake segments, but let's sum everything for simplicity
                total_sleep_mins += duration_sec / 60.0

        if date not in existing_sleep_dates:
            sleep_to_create.append(
                UserSleep(user_id=user_id, date=date, sleep_minutes=int(total_sleep_mins))
            )
    UserSleep.objects.bulk_create(sleep_to_create, ignore_conflicts=True)


def set_api_key(request):
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
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return None


def get_ai_response(request):
    if request.method == "POST":
        api_key = get_stored_api_key()
        if not api_key:
            return JsonResponse({"error": "No API key configured. Please set an API key first."}, status=400)

        try:
            body = json.loads(request.body)
            prompt = body.get("prompt", "").strip()
            if not prompt:
                return JsonResponse({"error": "Prompt is missing."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON input."}, status=400)

        sqlite_data = fetch_db_context()
        full_prompt = f"User Question: {prompt}\n\nDatabase Tables:\n{sqlite_data}"

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": SITE_URL,
                "X-Title": APP_NAME,
            }
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": full_prompt}],
            }
            response = requests.post(openrouter_url, headers=headers, data=json.dumps(payload))
            
            # Include additional debug log for API response
            # print(f"OpenRouter API Status: {response.status_code}")
            # print(f"OpenRouter Response Body: {response.text}")

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:  # Ensure choices exist
                    ai_response = choices[0].get("message", {}).get("content", "No response received.")
                    return JsonResponse({"response": ai_response})
                else:
                    return JsonResponse({"error": "No valid response from AI."}, status=500)
            else:
                error_message = f"OpenRouter error {response.status_code}: {response.text}"
                return JsonResponse({"error": error_message}, status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": f"Could not connect to OpenRouter: {str(e)}"}, status=500)


def fetch_db_context():
    """
    Reads all table names (except for django_*) from the SQLite database,
    grabs up to a few rows from each to give a sense of the data to the LLM.
    """
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'django_%';")
    tables = [row[0] for row in cursor.fetchall()]

    context_lines = []
    for tbl in tables:
        context_lines.append(f"TABLE: {tbl}")
        try:
            cursor.execute(f"SELECT * FROM {tbl} LIMIT 1000;")
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            context_lines.append(f"Columns: {', '.join(col_names)}")
            for row in rows:
                context_lines.append(f"Row: {row}")
        except Exception as e:
            context_lines.append(f"Error reading table {tbl}: {e}")
        context_lines.append("")

    conn.close()
    return "\n".join(context_lines)


def upload_csv_create_table(request):
    if request.method == "POST" and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Only CSV files are allowed.')
            return redirect('home')

        # Sanitize the table name
        table_name = os.path.splitext(csv_file.name)[0]
        table_name = "".join(x for x in table_name if x.isalnum() or x == '_').lower()

        file_data = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(file_data)
        rows = list(reader)
        if not rows:
            messages.error(request, 'CSV file is empty.')
            return redirect('home')

        headers = rows[0]
        data_rows = rows[1:]

        # Sanitize column names
        sanitized_headers = [f'"{h.strip()}"' for h in headers]

        conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        cursor = conn.cursor()

        # Create table with sanitized column names
        columns_def = ", ".join([f'{col} TEXT' for col in sanitized_headers])
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_def});'
        cursor.execute(create_stmt)

        # Insert data into the table
        placeholders = ", ".join(["?"] * len(headers))
        insert_stmt = f'INSERT INTO "{table_name}" ({", ".join(sanitized_headers)}) VALUES ({placeholders})'
        for row_data in data_rows:
            try:
                cursor.execute(insert_stmt, row_data)
            except sqlite3.OperationalError as e:
                print(f"Error inserting row {row_data}: {e}")
                messages.error(request, f"Error inserting data: {e}")
                conn.rollback()
                break

        conn.commit()
        conn.close()

        messages.success(request, f"CSV uploaded and table '{table_name}' created/updated.")
        return redirect('home')

    return redirect('home')

def list_tables_and_counts():
    conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
    cursor = conn.cursor()
    
    exclude_patterns = ("django_%", "auth_%", "sqlite_sequence")
    exclude_clause = " AND ".join([f"name NOT LIKE '{pattern}'" for pattern in exclude_patterns])
    
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {exclude_clause};")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_info = []
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM '{t}'")
        count = cursor.fetchone()[0]
        table_info.append((t, count))
    
    conn.close()
    return table_info


def drop_all_tables(request):
    """
    Drops all user-created tables in the SQLite database.
    Excludes system tables (django_*, auth_*, sqlite_sequence) and core app tables.
    Here we assume HR, Calories, and Sleep are also 'core' and exclude them.
    """
    if request.method == "POST":
        conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        cursor = conn.cursor()
        
        # Add the new model tables to exclusions
        exclude_patterns = (
            "django_%", 
            "auth_%", 
            "sqlite_sequence", 
            "stats_usersteps", 
            "manual", 
            "stats_userhr",
            "stats_usercalories",
            "stats_usersleep"
        )
        exclude_clause = " AND ".join([f"name NOT LIKE '{pattern}'" for pattern in exclude_patterns])
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND {exclude_clause};")
        tables = [row[0] for row in cursor.fetchall()]
        
        for tbl in tables:
            drop_stmt = f'DROP TABLE IF EXISTS "{tbl}"'
            cursor.execute(drop_stmt)
        
        conn.commit()
        conn.close()
        messages.success(request, "All user-created tables (except core tables) have been dropped.")
    return redirect('home')


def add_manual_data(request):
    if request.method == "POST":
        raw_input = request.POST.get("manual_input", "").strip()
        if not raw_input:
            messages.error(request, "No manual input provided.")
            return redirect('home')

        parts = [p.strip() for p in raw_input.split(",")]
        if len(parts) != 3:
            messages.error(request, "Please provide data in the format: YYYY-MM-DD, metric, value")
            return redirect('home')

        date_str, metric, value_str = parts
        try:
            date_val = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            value_val = float(value_str)
        except ValueError:
            messages.error(request, "Invalid date or value format.")
            return redirect('home')

        ManualData.objects.create(date=date_val, metric=metric, value=value_val)
        messages.success(request, "Manual data saved successfully.")
    return redirect('home')


def remove_last_manual_data(request):
    """
    Removes the most recently created manual data entry (if any).
    """
    last_entry = ManualData.objects.last()
    if last_entry:
        last_entry.delete()
        messages.success(request, "Last manual data entry was removed.")
    else:
        messages.info(request, "No manual data entries found to remove.")
    return redirect('home')
