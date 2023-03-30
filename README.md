# Dynatrace-Log-Monitoring-v1-Conversion-Scripts

## This is not a supported product by Dynatrace, this is a tool I built to help my client migrate over. 

If you have found this repository, you are looking for a way to migrate your Dynatrace environment from log monitoring v1 over to Log Monitoring Classic (v2). I want to mention that this tool is in no way perfect, and there still does require some manual intervention. You will have to go into the generated CSV files and modify the new log queries to be proper.

## What this is?

This is a tool to help you prepare for the migration. These series of scripts will allow you to get your current configurations, create a csv file that will try to format your existing events and metrics to the new log queries.

## How to use

Step 1. pip install -r requirements.txt

Step 2. Go into each script and add in the tenant URL (should not end in a /) as well as your Dynatrace API Token. The token scopes required are read.entities, settings read/write.

Step 3. Using the command line, run python <Filename> to run the script.


## What it does

Get Events will generate a CSV file that will be in a new log event format which will then be used to upload those events once you have migrated to v2. 
Get metrics will get the metrics, get sources will create a file that tells you the host, process, log path selected.

Upload events and metrics have a built in test-mode functionality. By default MAKE_CHANGE_MODE is set to False. This is so you can run the API calls against the /validator API which will allow you to pre-emptively confirm you will sucessfully be able to migrate to v2. Some events and metrics may fail validation. This can happen for a number of reasons whether the query is too complex and it needs to use maybe a dt.host_group.id value rather than a list of 35 hosts.