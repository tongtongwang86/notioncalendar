import os
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# Notion API setup
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL = "https://api.notion.com/v1/databases/{}/query".format(NOTION_DATABASE_ID)

# Google Calendar API setup
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "your-private-key-id",
    "private_key": os.getenv("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL"),
    "client_id": "your-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "your-cert-url",
}

# Fetch events from Notion
def fetch_notion_events():
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    response = requests.post(NOTION_API_URL, headers=headers)
    response.raise_for_status()
    results = response.json()["results"]
    events = []
    for result in results:
        if "properties" in result:
            props = result["properties"]
            event = {
                "name": props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content"),
                "start": props.get("Start", {}).get("date", {}).get("start"),
                "end": props.get("End", {}).get("date", {}).get("end"),
            }
            events.append(event)
    return events

# Post events to Google Calendar
def post_to_google_calendar(events):
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    service = build("calendar", "v3", credentials=creds)

    for event in events:
        event_body = {
            "summary": event["name"],
            "start": {"dateTime": event["start"], "timeZone": "UTC"},
            "end": {"dateTime": event["end"], "timeZone": "UTC"},
        }
        service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event_body).execute()

# Main function
if __name__ == "__main__":
    notion_events = fetch_notion_events()
    post_to_google_calendar(notion_events)
