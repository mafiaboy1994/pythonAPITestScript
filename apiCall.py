#import adal
import msal 
import requests 
import string
import json
import os
import logging
import re
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
from azure.mgmt.storage import StorageManagementClient
from urllib.parse import quote
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.database as cosmos_database
from azure.cosmos import PartitionKey, exceptions
load_dotenv()

#Load OS Environment Variables
keyvault_name = os.environ['KEY_VAULT_NAME']
subId = os.environ['SUBSCRIPTION_ID']
client_ID = os.environ['CLIENT_ID']
tenant_ID = os.environ['TENANT_ID']
client_secret = os.environ['CLIENT_SECRET']
authority_url = os.environ['AZURE_AUTHORITY_HOST']
cosmos_db_account=os.environ["COSMOS_DB_URI"]
cosmos_db_key=os.environ['COSMOS_DB_KEY']



config={
    'authority': authority_url+tenant_ID,
    'client_id':client_ID,
    'client_secret': client_secret,
    #'scope': ["https://graph.microsoft.com/.default"]
    'scope': ["https://management.azure.com/.default"]
}



#standard Vars
keyname='sasecret'

#containerVariables
dbName='storageAccounts'
containerName='accountInfo'

#dictionaries
subscription_info = {}




def azureADApplicationConnect(config,tenant_ID): #client_ID,tenant_ID,client_secret):
    
    #Set's Authority for endpoint auth for Azure AD App Registration
    authority = config["authority"]
    
    #Client Connection
    msal_app = msal.ConfidentialClientApplication(
        client_id=config["client_id"], 
        authority=config["authority"],
        client_credential=config["client_secret"]
    )

    result = msal_app.acquire_token_silent(
        scopes=config['scope'],
        account=None,
    )    
    
    #if nothing stored in result, get token
    if not result:
        result = msal_app.acquire_token_for_client(scopes=config['scope'])
    
    #if token already exists then print result
    if "access_token" in result:
        print("access token found")
        #print(result["access_token"])
    else:
        print(result["error"])
        print(result["error_description"])
        print(result["correlation_id"])
    
    return result["access_token"]

#print(azureADApplicationConnect(config,tenant_ID))    

saEndpoint = f"https://management.azure.com/subscriptions/{subId}/providers/Microsoft.Storage/storageAccounts?api-version=2022-09-01"




def storageApiCall(saEndpoint):
    access_token = azureADApplicationConnect(config,tenant_ID)
    #print(access_token)
    #headers = {"Authorization": 'Bearer ' + access_token}    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    #print(headers)
    json_output = requests.get(saEndpoint, headers=headers).json()
    
    return json_output


raw_data = storageApiCall(saEndpoint)
#print(raw_data)

#print(raw_data["value"])

# Blank Dictionary to get 
storageAccountsData = []


def cosmosDBApiCall(cosmos_db_account,cosmos_db_key):
    client = cosmos_client.CosmosClient(cosmos_db_account,{'masterKey': cosmos_db_key})
    #databases = list(client.list_databases())
    
    
    return client

#cosmosDBApiCallResponse = cosmosDBApiCall(cosmos_db_account=cosmos_db_account,cosmos_db_key=cosmos_db_key)
#print(cosmosDBApiCallResponse)

#Get's Containers
def cosmosDBContainers(cosmos_db_account,cosmos_db_key):
    apiCall = cosmosDBApiCall(cosmos_db_account=cosmos_db_account, cosmos_db_key=cosmos_db_key)
    db = apiCall.get_database_client('storageAccounts')
    containers = db.get_container_client('accountInfo')
    
    return containers

dbContainer = cosmosDBContainers(cosmos_db_account,cosmos_db_key)

def fc_read_item(container, doc_id):
    read_item = container.read_item(item=doc_id, partition_key=doc_id)
    return read_item

#insert items
def cosmosDBStorageAccountInfoInsert(dbContainer,storageAccountsData):
    #DBContainerSearchFun = cosmosDBContainersSearch(dbName)
    #GetContainerClient = DBContainerSearchFun.get_container_client(container=containerName)
    
    
    #for i,entry in enumerate(raw_data["value"], start=0)    
    
    #for i,storageAccount in storageAccountDataCleaned:
    #for i, storageAccount in enumerate(storageAccountDataCleaned, start=0):
    
    containerTest = dbContainer
    
    CreateItem = containerTest.create_item(body=storageAccountsData)
    #createItem = dbContainer.create_item(body=storageAccountsData)
    #return containerTest

#read_item=fc_read_item(dbContainer,'0')
#print(read_item)


def cosmosDBContainersSearch(dbName,containerName):

        #print('creating.......')
        dbCreate=cosmos_client.CosmosClient.create_database_if_not_exists(id=dbName,partition_key='/id',self=cosmos_client.CosmosClient(url=cosmos_db_account,credential=cosmos_db_key))
        dbCreateConv=str(dbCreate)
        #containerCreate = cosmos_database.DatabaseProxy.create_container_if_not_exists(id=containerName,partition_key='/id', self=cosmos_client.CosmosClient(url=cosmos_db_account,credential=cosmos_db_key))
        GetDBClient=cosmos_client.CosmosClient.get_database_client(database=dbName,self=cosmos_client.CosmosClient(url=cosmos_db_account,credential=cosmos_db_key))
        containerCreate=GetDBClient.create_container_if_not_exists(id=containerName,partition_key=PartitionKey(path='/id'))
        #cosmos_client.CosmosClient.get_database_client(self=cosmos_client.CosmosClient(cosmos_db_account,cosmos_db_key),database=dbName)
        return dbCreate
        #print(GetDBClient)

def storageAccountDataCleanup(raw_data,storageAccountsData,dbContainer):
    for i,entry in enumerate(raw_data["value"], start=0):
        try:
            #replace Resource ID characters
            subscriptionsReplace = entry['id'].replace("/subscriptions/", "")
            newID = subscriptionsReplace.replace("/","_")
            #newID.replace('_subscriptions', '')
            saItems = {
                'id': newID,
                'name': entry["name"],
                'location': entry["location"],
                'skuName': entry["sku"]["name"],
                'skuTier': entry["sku"]["tier"] 
            }
            storageAccountsData.append(saItems)
        
            #Call cosmos DB API
            #Read items in cosmos DB, insert if values have changed
            
            var_id = saItems['id']
            var_name = saItems["name"]

            var_item = fc_read_item(dbContainer,var_id)
            #print(var_item)
            
            result=cosmosDBStorageAccountInfoInsert(dbContainer,saItems)
                
        except exceptions.CosmosResourceNotFoundError:
            pass
            print(f"{var_name} item not found")
            print(f"inserting {var_name} item")
            result=cosmosDBStorageAccountInfoInsert(dbContainer,saItems)
            #print(result)
        
        except exceptions.CosmosResourceExistsError:
            pass
            print(f"{var_name} item found")
            print(f"updating {var_name} item")
        
        #if var_item:
            #print(f'also found item {var_item} in search')
                
    #return storageAccountsData

#uncomment the below
storageAccountDataCleaned=storageAccountDataCleanup(raw_data,storageAccountsData,dbContainer)


#print(storageAccountDataCleaned)

#cosmosDBApiEndpoint = f"https://{cosmos_db_account}.documents.azure.com/dbs"



#uncomment the below
#cosmosdbcontainersresult=cosmosDBContainers(cosmos_db_account,cosmos_db_key)

#print(cosmosdbcontainersresult)



#search containers
#Below not called or used

     


        

#uncomment the below
#cosmosDBStorageAccountInfoInsert(dbName,storageAccountDataCleaned)