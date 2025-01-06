import json
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests

# Load environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Notion and Google API URLs and credentials
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Google Calendar service
def get_google_calendar_service():
    credentials = Credentials.from_service_account_info(
        json.loads(GOOGLE_SERVICE_ACCOUNT_JSON), scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

# Fetch events from Notion database
def fetch_notion_events():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=NOTION_HEADERS)
    response.raise_for_status()
    data = response.json()
    events = []

    # Parse events from Notion database
    for result in data.get("results", []):
        props = result.get("properties", {})
        title = props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "No Title")
        date = props.get("Date", {}).get("date", {}).get("start")

        if title and date:
            events.append({"summary": title, "start": date, "end": date})
    return events

# Post events to Google Calendar
def post_to_google_calendar(events):
    service = get_google_calendar_service()
    for event in events:
        event_body = {
            "summary": event["summary"],
            "start": {"dateTime": event["start"], "timeZone": "UTC"},
            "end": {"dateTime": event["end"], "timeZone": "UTC"},
        }
        service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event_body).execute()
        print(f"Event '{event['summary']}' added to Google Calendar.")

# Main script execution
if __name__ == "__main__":
    try:
        print("Fetching events from Notion...")
        notion_events = fetch_notion_events()
        print(f"Found {len(notion_events)} events in Notion.")
        print("Syncing events to Google Calendar...")
        post_to_google_calendar(notion_events)
        print("Sync complete.")
    except Exception as e:
        print("An error occurred:", e)
