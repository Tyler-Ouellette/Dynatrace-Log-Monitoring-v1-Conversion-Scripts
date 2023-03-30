import requests
requests.packages.urllib3.disable_warnings()
import json
import pandas as pd
import time

## This script takes the output csv from get_events.py and creates new Log v2 events in Dynatrace
## It will first check to see if there is already an event with the same name before hitting the setting api for the event

filename = 'logv2events_LOG_PATTERN_V3_Config.csv' # NEW FILE JUST CREATED
url = ''
token = ''


# If this is true, then the script will make the change to Dynatrace. Otherwise it will only send test configs.
MAKE_CHANGE_MODE = False

headers= { 'Authorization': 'Api-Token ' + token,
           'Content-Type': 'application/json'}

def main():

    start = time.time()

    # Get existing list of events to double check for existing
    req = requests.get(url + "/api/v2/settings/objects?schemaIds=builtin%3Alogmonitoring.log-events&scopes=environment&fields=objectId%2Cvalue", headers=headers, verify=False)
    settings = json.loads(req.content)

    existing_event_names = []

    for item in settings["items"]:
        existing_event_names.append(item["value"]["summary"])

    print(existing_event_names)

    # Importing CSV for events to upload
    df = pd.read_csv(filename)

    for index, logevent in df.iterrows():
        print("Creating Log Event: " + logevent['Summary'])

        if logevent['Summary'] in existing_event_names:
            print("Log Event with name already exists. Skipping.")
            continue


        eventTemplate = { "title": logevent['Title'],
                          "description": "{content}",
                          "eventType": logevent['Event Type'].upper(),
                          "davisMerge": True,
                          "metadata": [{ "metadataKey": "Log Source", "metadataValue": "{log.source}" }, {"metadataKey": "Host Name", "metadataValue": "{host.name}" }] }

        value = { "enabled": False,
                  "summary": logevent['Summary'],
                  "query": logevent['Log Query'],
                  "eventTemplate": eventTemplate }
            
        payload = { "schemaId": "builtin:logmonitoring.log-events",
                    "scope": "environment",
                    "value": value }

        data = []
        data.append(payload)

        #print(data)
        if MAKE_CHANGE_MODE == True:
            post = requests.post(url + "/api/v2/settings/objects", data=json.dumps(data), headers=headers, verify=False)
        else:
            post = requests.post(url + "/api/v2/settings/objects?validateOnly=true", data=json.dumps(data), headers=headers, verify=False)
        
        print(post.status_code)
        if post.status_code == 400:
            print(post.text)

    end = time.time()
    print(f"Runtime of the program is {end - start}")


if __name__ == "__main__":
    main()

