import requests
import json
import pandas as pd
import time

## This script reads a prod.json which is an extract of the v1 Log Events screen, done by Michael Dec and his dev team
## It parses the events and gets the process and host names back via API.
## It then converts the existing configs into Log v2 compatible configurations and exports it to a csv.

filename = 'LOG_PATTERN_V3_Config.json'
url = ''
token = ''


headers= { 'Authorization': 'Api-Token ' + token }


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
    h = tohex(host['longId'], 64)
    # remove 0x notation and convert to uppercase
    h = h.upper()[2:].replace('X', 'x')
    print(h)
    
    req = requests.get(url + "/api/v2/entities/HOST-" + h, headers=headers, verify=False)
    j = json.loads(req.content)


    try:
        print(j['displayName'])
        return j['displayName']
    except:
        return "Host Not Found"

# query dynatrace for host name
def get_hostOAVersion(host):  
    h = tohex(host['longId'], 64)
    # remove 0x notation and convert to uppercase
    h = h.upper()[2:].replace('X', 'x')
    # print(h)
    
    req = requests.get(url + "/api/v2/entities/HOST-" + h, headers=headers, verify=False)
    j = json.loads(req.content)

    try:
        # print(j['agentVersion'])
        # print(j['agentVersion']['minor'])
        return j['agentVersion']['minor']
    except:
        print("host not found")
        return "Not Host Based"

# query dynatrace for process group name
def get_process(process):
    h = tohex(process['longId'], 64)
    # remove 0x notation and convert to uppercase
    h = h.upper()[2:].replace('X', 'x')
    
    req = requests.get(url + "/api/v2/entities/PROCESS_GROUP-" + h, headers=headers, verify=False)
    j = json.loads(req.content)

    # print(j)
    try:
        #print(j['displayName'])
        return (j['displayName'])
    except:
        return "Process doesn't exist"

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
    versions = []
    sources = []
    
    for p in filters['pathDefinitions']:
        paths.append(p['definition'])

    for h in filters['hostFilters']:
        hosts.append(get_hostname(h))
        # versions.append(get_hostOAVersion(h))

    for s in filters['sourceEntities']:
        sources.append(get_process(s))

    if len(sources) == 0:
        sources.append(get_OS_process(filters))

    if len(hosts) == 0:
        hosts.append("ALL")

    found_filters = {}
    found_filters["sources"] = sources
    found_filters["paths"] = paths
    found_filters["hosts"] = hosts
    # found_filters["version"] = versions

    return found_filters


def create_search(search):
    search_query = search
    
    # check for escape characters (unclear in documentation what will work)
    escape_characters = ['=', '\\']
    for char in escape_characters:
        if char in search:
            print("Found " + char + " in search")

    return search_query

def create_processgroup(found_filters):
    query = "("
    sources = []
    print(found_filters)
    for f in found_filters:
        for source in f["sources"]:
            sources.append(source)

    query_sources = list(dict.fromkeys(sources))
    
    for source in query_sources:
        query = query + "dt.process.name=\"" + source + "\" OR "

    if len(query) == 1:
        return ""

    query = query.rstrip(" OR ") + ")"
    
    #print(query)
    return query


def create_OS_query(found_filters):
    # find the system log paths
    path_query = "("
    paths = []
    for f in found_filters:
        for path in f["paths"]:
            paths.append(path)

    paths = list(dict.fromkeys(paths))
    path_query = path_query + "log.source=\"" + path + "\" OR "

    path_query = path_query.rstrip(" OR ") + ")"
    
    # find the hosts
    host_query = "("
    hosts = []
    for f in found_filters:
        for host in f["hosts"]:
            hosts.append(host)

    hosts = list(dict.fromkeys(hosts))
    if len(hosts) == 1 and hosts[0] == "ALL":
        host_query = ""
    else:
        for host in hosts:
            if host != "ALL":
                host_query = host_query + "host.name=\"" + host + "\" OR "
        host_query = host_query.rstrip(" OR ") + ")"

    if len(path_query) == 2 or len(host_query) == 2:
        # print("path or hosts has a problem in OS event")
        return ""

    if len(host_query) == 0:
        return path_query

    return path_query + " AND " + host_query
    

# create a Log v2 style query from original log event details
def create_query(event, found_filters):
    query = ""
    
    # create string search part of query
    query = query + create_search(event["searchString"])

    # create process group part of query
    processgroup = create_processgroup(found_filters)

    # if process group is OS log, then create path and host part of query
    if "Windows Operating System" in processgroup or "Linux Operating System" in processgroup:
        query = query + " AND " + create_OS_query(found_filters)
    else:
        query = query + " AND " + processgroup

    return query
    
    
def generate_row(event):
    found_filters = []
    for f in event['logSourceFilters']:
        found_filters.append(find_filters(f))
        # print(found_filters)
        
    query = create_query(event, found_filters)

    description = "Imported Log v1 Event." # Originally created by " + event['auditInfo']['user']
    
    # print(found_filters)
    row = [event['id'], event['patternName'], event['searchString'], query, event['patternName'], description, "CUSTOM_ALERT"] 
    # row = [event['id'], event['patternName'], event['searchString'], query, event['patternName'], description, "Error", found_filters[0]['version']] 

    # print(row)
    return row



def main():
    logevents = []
    data = read_json()

    start = time.time()
    
    for event in data:
        logevents.append(generate_row(event))

    data_columns = ['Log Event Orig ID', 'Summary', "Orig Search", 'Log Query', 'Title', 'Description', 'Event Type']
    # data_columns = ['Log Event Orig ID', 'Summary', "Orig Search", 'Log Query', 'Title', 'Description', 'Event Type', 'Agent Version']
    df = pd.DataFrame(data = logevents, columns=data_columns)
    #print (df)
    
    df.to_csv("logv2events_" + filename.rstrip(".json") + ".csv", encoding='utf-8', index=False)

    end = time.time()
    print(f"Runtime of the program is {end - start}")


if __name__ == "__main__":
    main()

