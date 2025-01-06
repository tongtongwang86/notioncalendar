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
        date = props.get("due date", {}).get("date", {}).get("start")  # Updated key to match "due date"
        description = ""
        rich_text = props.get("description", {}).get("rich_text", [])
        if rich_text:
            description = rich_text[0].get("text", {}).get("content", "")

        if title and date:
            events.append({
                "summary": title,
                "start": date,
                "end": date,
                "description": description
            })
    return events

# Fetch existing events from Google Calendar
def fetch_google_calendar_events():
    service = get_google_calendar_service()
    events_result = service.events().list(calendarId=GOOGLE_CALENDAR_ID).execute()
    google_events = events_result.get("items", [])
    existing_events = set()

    for event in google_events:
        summary = event.get("summary")
        start_date = event.get("start", {}).get("dateTime", "").split("T")[0]
        if summary and start_date:
            existing_events.add((summary, start_date))
    return existing_events

# Post events to Google Calendar, avoiding duplicates
def post_to_google_calendar(events):
    service = get_google_calendar_service()
    existing_events = fetch_google_calendar_events()
    for event in events:
        # Check if event already exists in Google Calendar
        if (event["summary"], event["start"]) in existing_events:
            print(f"Event '{event['summary']}' already exists. Skipping...")
            continue

        event_body = {
            "summary": event["summary"],
            "description": event["description"],  # Include description in event body
            "start": {"dateTime": f"{event['start']}T00:00:00Z", "timeZone": "UTC"},
            "end": {"dateTime": f"{event['end']}T23:59:59Z", "timeZone": "UTC"},
        }
        service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event_body).execute()
        print(f"Event '{event['summary']}' added to Google Calendar with description.")

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
