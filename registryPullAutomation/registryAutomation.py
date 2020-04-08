import nipyapi
import json
import ast
import os
import sys

#1. Formats API call and converts to dictionary
def formatDict(dict):
  strBucket = str(dict)
  formatBucket = strBucket.replace('\n','')
  convertToDict = ast.literal_eval(formatBucket)  
  return convertToDict

#1. revertsLocalChanges made on failover cluster
def revertLocalChanges(id,identifier):
  process_group = nipyapi.canvas.get_process_group(identifier, identifier_type='name')
  nipyapi.canvas.schedule_process_group(id,False)
  os.system('sleep 1')
  nipyapi.versioning.revert_flow_ver(process_group)
  os.system('sleep 1')
  nipyapi.canvas.schedule_process_group(id,True)
  os.system('sleep 1')
  
#1. Converts format from bucket type to json(dictionary) format and grabs ID of all buckets
def convertToJson(buckets):
  jsonBuckets = []
  for bucket in buckets:
    convertToDict = formatDict(bucket)
    jsonBuckets.append(convertToDict['identifier'])
  return jsonBuckets

#1. Checks to see if this is the primary cluster
def checkIfPrimaryCluster():
  root = nipyapi.canvas.get_root_pg_id()
  process_group = nipyapi.canvas.get_process_group(root, identifier_type='id')
  var = nipyapi.canvas.get_variable_registry(process_group)
  convertToDict = formatDict(var)
  variables = convertToDict['variable_registry']['variables']
  
  #Grab all variables in the registry
  for variable in variables:
    variableName = variable['variable']['name'].lower()
    variableValue = variable['variable']['value'].lower()
    if variableName == "cluster.isprimary" and variableValue == "true":
      return True
  return False
 
#1. For all the buckets in the NiFi registry,
#2. creates a dictionary that stores the flow name in the registry, along with particular attributes (Bucket_id,flow_id,latest_version)
def getRegistryFlowsInfo(listOfBucketIds):
  finalDict = {}
  for bucket_id in listOfBucketIds:
    flowInfo = nipyapi.versioning.list_flows_in_bucket(bucket_id)
    for flow in flowInfo:
      convertToDict = formatDict(flow)
      attributes = [convertToDict['bucket_identifier'],convertToDict['identifier'],convertToDict['version_count']]
      finalDict[convertToDict['name']]=attributes
  return finalDict

#1. Gets all the process groups on the canvas (Including sub process groups)
#2. Checks for 'STALE' and 'LOCALLY_MODIFIED_AND_STALE' (out of date) process groups
#3. If out of date, adds the name of progress group on the canvas and the flow name that's in NiFi Registry to dictionary**
def getOutOfDateFlows():
  finalDict = {}
  root = nipyapi.canvas.get_root_pg_id()
  groups = nipyapi.canvas.list_all_process_groups(root)
  for flow in groups:
    convertToDict = formatDict(flow)
    #print(convertToDict)
    id = convertToDict['component']['id']
    if convertToDict['versioned_flow_state'] == 'STALE':
      #attributes = [convertToDict['component']['version_control_information']['flow_name']]
      finalDict[convertToDict['component']['name']]=convertToDict['component']['version_control_information']['flow_name']
    elif convertToDict['versioned_flow_state'] == 'LOCALLY_MODIFIED_AND_STALE':
      identifier = convertToDict['component']['name']
      revertLocalChanges(id,identifier)
      finalDict[convertToDict['component']['name']]=convertToDict['component']['version_control_information']['flow_name']
  return finalDict

#1. Checks if there are any PG out of date from function above
#2. If there is, takes the progress group id from canvas, maps it to flow name in the registry, gets latest version and updates PG
def updateFlows(outOfDateDict,registryFlowInfoDict):
  if not outOfDateDict:
   sys.exit()
  for identifier,version_name in outOfDateDict.items():
    for registry_name,values in registryFlowInfoDict.items():
      if version_name == registry_name:
        process_group = nipyapi.canvas.get_process_group(identifier, identifier_type='name')
        latest_version = values[2]
        nipyapi.versioning.update_flow_ver(process_group,latest_version)

if __name__ == '__main__':
  #Configure these variable
  nipyapi.config.nifi_config.host = 'http://cdf-west-nifi-1.coop-west.local:9090/nifi-api' #Cluster to check
  nipyapi.config.nifi_config.verify_ssl = False
  nipyapi.config.registry_config.host = 'http://cdf-east-nifi-1.coop-east.local:61080/nifi-registry-api' #Common Registry

  if checkIfPrimaryCluster():
    sys.exit()
  
  buckets = nipyapi.versioning.list_registry_buckets()
  jsonFormatBuckets = convertToJson(buckets)
  registryFlowInfoDict = getRegistryFlowsInfo(jsonFormatBuckets)
  outOfDateDict = getOutOfDateFlows()
  updateFlows(outOfDateDict,registryFlowInfoDict) 

