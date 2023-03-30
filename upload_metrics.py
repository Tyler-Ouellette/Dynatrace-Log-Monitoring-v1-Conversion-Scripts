import requests
requests.packages.urllib3.disable_warnings()
import json
import pandas as pd
import time

## This script takes the output csv from get_metrics.py and creates new Log v2 metrics in Dynatrace
## It will first check to see if there is already an metric with the same name before hitting the setting api for the metric

filename = 'logv2metrics_LOG_METRIC_REGISTRATION_Config.csv' # NEW FILE JUST CREATED
url = ''
token = ''


# If this is true, then the script will make the change to Dynatrace. Otherwise it will only send test configs.
MAKE_CHANGE_MODE = False

headers= { 'Authorization': 'Api-Token ' + token,
           'Content-Type': 'application/json'}

def main():

    start = time.time()

    # Get existing list of metrics to double check for existing
    # req = requests.get(url + "/api/v2/settings/objects?schemaIds=builtin%3Alogmonitoring.log-metrics&scopes=environment&fields=objectId%2Cvalue", headers=headers)
    req = requests.get(url + "/api/v2/settings/objects?schemaIds=builtin:logmonitoring.schemaless-log-metric&scopes=environment&fields=objectId%2Cvalue", headers=headers, verify=False)
    settings = json.loads(req.content)

    existing_metric_names = []

    for item in settings["items"]:
        existing_metric_names.append(item["value"]["Log Metric Key"])

    # print(existing_metric_names)

    # Importing CSV for metrics to upload
    df = pd.read_csv(filename)

    for index, logmetric in df.iterrows():
        print("Creating Log metric: " + logmetric['Log Metric Key'])

        if logmetric['Log Metric Key'] in existing_metric_names:
            print("Log metric with name already exists. Skipping.")
            continue


        # metricTemplate = { "title": logmetric['Title'],
        #                   "description": "{content}",
        #                   "metricType": logmetric['metric Type'].upper(),
        #                   "davisMerge": True,
        #                   "metadata": [{ "metadataKey": "Log Source", "metadataValue": "{log.source}" }, {"metadataKey": "Host Name", "metadataValue": "{host.name}" }] }

        value = { "enabled": False,
                  "key": logmetric['Log Metric Key'],
                  "query": logmetric['Log Query'],
                  "measure": "OCCURRENCE" }
            
        payload = { 
                    "schemaId": "builtin:logmonitoring.schemaless-log-metric",
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
        if post.status_code == 400 or post.status_code == 404:
            # print(logmetric['Log Metric Key'])
            print(post.text)

    end = time.time()
    print(f"Runtime of the program is {end - start}")


if __name__ == "__main__":
    main()

