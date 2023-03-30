import requests
import json
import pandas as pd
import time

## This script reads a prod.json which is an extract of the v1 Log Events screen, done by Michael Dec and his dev team
## It parses the events and gets the process and host names back via API.
## Then it generates a csv of all the Log Sources that need to be enabled to support the existing Events in v2

filename = 'LOG_PATTERN_V3_Config.json'
url = ''
token = ''


headers= { 'Authorization': 'Api-Token ' + token,
           'Content-Type': 'application/json'}


def read_json():
    f = open(filename, encoding="utf8")
    data = json.load(f)           
    f.close()
    return data


# signed int to hex conversion (two's complement)
def tohex(val, nbits):
  return hex((val + (1 << nbits)) % (1 << nbits))


# query dynatrace for host name
def get_hostname(host):        
    try:
        h = tohex(host['longId'], 64)    
        # remove 0x notation and convert to uppercase
        h = h.upper()[2:].replace('X', 'x')
        
        req = requests.get(url + "/api/v1/entity/infrastructure/hosts/HOST-" + h, headers=headers, verify=False)
        j = json.loads(req.content)

        return j['displayName']
    except:
        return "Unknown"

# query dynatrace for process group name
def get_process(process):
    try:
        h = tohex(process['longId'], 64)
        
        # remove 0x notation and convert to uppercase
        h = h.upper()[2:].replace('X', 'x')
        
        req = requests.get(url + "/api/v1/entity/infrastructure/process-groups/PROCESS_GROUP-" + h, headers=headers, verify=False)
        j = json.loads(req.content)

        return (j['displayName'])
    except:
        return "Unknown"

# if process group can't be found, see if this filter is an OS system log instead
def get_OS_process(filters):
    try:
        if filters['osTypes'][0] == "OS_TYPE_WINDOWS":
            return "Windows Operating System"
        elif filters['osTypes'][0] == "OS_TYPE_LINUX":
            return "Linux Operating System"
        else:
            return "Unknown"
    except:
        return "Unknown"

# check each logSourceFilters object and produce a set of source rows
def find_filters(filters):
    paths = []
    hosts = []
    sources = []
    
    for p in filters['pathDefinitions']:
        paths.append(p['definition'])

    for h in filters['hostFilters']:
        hosts.append(get_hostname(h))

    for s in filters['sourceEntities']:
        sources.append(get_process(s))

    if len(sources) == 0:
        sources.append(get_OS_process(filters))

    if len(hosts) == 0:
        hosts.append("ALL")

    filter_rows = []
    for s in sources:
        for p in paths:
            for h in hosts:
                #print (s + " " + p + " " + h)
                filter_rows.append([s,p,h])

    return filter_rows
    
    
def generate_rows(event):
    rows = []
    for f in event['logSourceFilters']:
        found = find_filters(f)
        for r in found:
            row = [event['id'], event['patternName'], event['searchString']] + r
            print(row)
            rows.append(row)

    return rows


def main():
    sources = []
    data = read_json()

    start = time.time()
    
    for event in data:
        for row in generate_rows(event):
            sources.append(row)
    
    data_columns = ['Log Event ID', 'Pattern Name', 'Search String', 'Process Group', 'Path Definition', "Host"]
    df = pd.DataFrame(data = sources, columns=data_columns)
    
    df.to_csv("sources_" + filename.rstrip(".json") + ".csv", encoding='utf-8', index=False)
    
    end = time.time()
    print(f"Runtime of the program is {end - start}")


if __name__ == "__main__":
    main()

