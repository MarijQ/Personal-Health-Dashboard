import os
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import time

# Update with your client secret JSON path
CLIENT_SECRET_FILE = "client_secret.json"
CREDENTIALS_FILE = "google_fit_token.json"
SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read']

end_time_millis = int(time.time() * 1000)  # Current time in milliseconds
start_time_millis = end_time_millis - (90 * 24 * 60 * 60 * 1000)  # 90 days


def authenticate():
    """Authenticate and return Google Fit credentials."""
    creds = None
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
    # If no valid credentials, perform OAuth Flow
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=8080)
        # Save the credentials for future use
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds


def fetch_steps_data(creds):
    """Fetch steps data from Google Fit."""
    url = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate'
    headers = {'Authorization': f'Bearer {creds.token}'}

    # Request body for querying steps data
    body = {
        "aggregateBy": [{
            "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas",
            "dataTypeName": "com.google.step_count.delta",
        }],
        "bucketByTime": {"durationMillis": 86400000},  # Daily buckets
        "startTimeMillis": start_time_millis,
        "endTimeMillis": end_time_millis
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


def save_to_csv(data):
    """Save steps data to a CSV file."""
    if not data or 'bucket' not in data:
        print("No data to save.")
        return

    output_file = "steps_data.csv"
    with open(output_file, 'w') as file:
        file.write("date,steps\n")  # CSV Header
        for bucket in data['bucket']:
            start_timestamp = int(bucket['startTimeMillis']) // 1000
            date = time.strftime('%Y-%m-%d', time.gmtime(start_timestamp))
            steps = sum([point['value'][0]['intVal']
                        for point in bucket['dataset'][0]['point']])
            file.write(f"{date},{steps}\n")
    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    creds = authenticate()
    steps_data = fetch_steps_data(creds)
    save_to_csv(steps_data)
