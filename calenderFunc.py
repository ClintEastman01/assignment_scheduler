from __future__ import print_function
import googleLogin
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

creds = googleLogin.login()
service = build('calendar', 'v3', credentials=creds)


def check_event(start_time, summary):
    # checks next 30 events in calendar to see if the event that is trying to be created already exist
    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=30, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if start == start_time and event['summary'] == summary:
                return True

    except HttpError as error:
        print('An error occurred: %s' % error)

    return False


def create_events(events):
    # This creates the events that were passed by calendar details and is checked to make sure it will not be duplicated
    events_added = []
    for event in events:
        try:
            task_name = event[0]
            task_type = event[1]
            class_name = event[2]
            start_time = event[3]
            endtime = event[4]
            remind1 = event[5]
            remind2 = event[6]

            if check_event(start_time, task_name):
                continue
            if not check_event(start_time, task_name):
                event = {
                    'summary': task_name,
                    'description': task_type + ' for ' + class_name,
                    'start': {
                        'dateTime': start_time,
                        'timeZone': 'America/New_York',
                    },
                    'end': {
                        'dateTime': endtime,
                        'timeZone': 'America/New_York',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': remind1},
                            {'method': 'popup', 'minutes': remind2},
                        ],
                    },
                }
                service.events().insert(calendarId='primary', body=event).execute()

                if class_name in events_added:
                    continue
                else:
                    events_added.append(class_name)

        except Exception:
            events_added.append(events[len(events) - 1])
    return events_added


if __name__ == '__main__':
    pass
