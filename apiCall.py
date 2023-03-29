#import adal
import msal 
import requests 
import string
import json
import os
import logging
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
from azure.mgmt.storage import StorageManagementClient
from urllib.parse import quote
import azure.cosmos.cosmos_client as cosmos_client
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

#print(raw_data["value"])

# Blank Dictionary to get 
storageAccountsData = []

def storageAccountDataCleanup(raw_data,storageAccountsData):

    for i,entry in enumerate(raw_data["value"], start=0):

        saItems = {
            'id': "{}".format(i),
            'name': entry["name"],
            'location': entry["location"],
            'skuName': entry["sku"]["name"],
            'skuTier': entry["sku"]["tier"] 
        }
        storageAccountsData.append(saItems)
    return storageAccountsData

storageAccountDataCleaned=storageAccountDataCleanup(raw_data,storageAccountsData)
#print(storageAccountDataCleaned)

cosmosDBApiEndpoint = f"https://{cosmos_db_account}.documents.azure.com/dbs"

def cosmosDBApiCall(cosmos_db_account,cosmos_db_key):
    client = cosmos_client.CosmosClient(cosmos_db_account,{'masterKey': cosmos_db_key})
    databases = list(client.list_databases())
    
    for database in databases:
        print(database['id'])
    return databases

cosmosDBApiCallResponse = cosmosDBApiCall(cosmos_db_account=cosmos_db_account,cosmos_db_key=cosmos_db_key)
print(cosmosDBApiCallResponse)

#cosmosDBApiResponse = cosmosDBApiCall(cosmosDBApiEndpoint)
#print(cosmosDBApiResponse)