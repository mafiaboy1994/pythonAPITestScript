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
from dotenv import load_dotenv

load_dotenv()

#Load OS Environment Variables
keyvault_name = os.environ['KEY_VAULT_NAME']
subId = os.environ['SUBSCRIPTION_ID']
client_ID = os.environ['CLIENT_ID']
tenant_ID = os.environ['TENANT_ID']
client_secret = os.environ['CLIENT_SECRET']

config={
    'authority': f"https://login.microsoftonline.com/{tenant_ID}",
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
    authority = f"https://login.microsoftonline.com/{tenant_ID}"
    
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
        
    
def keyVaultConnect(keyvault_name,tenant_ID,client_ID,client_secret,keyname):
    #set's vars for KV connection & credentials
    KVUri = f"https://{keyvault_name}.vault.azure.net"
    credential = ClientSecretCredential(tenant_ID,client_ID,client_secret)
    client = SecretClient(vault_url=KVUri, credential=credential)
    sasecret=client.get_secret(keyname)

endpoint = f"https://management.azure.com/subscriptions?api-version=2020-01-01"

def apiCall(endpoint):
    access_token = azureADApplicationConnect(config,tenant_ID)
    #print(access_token)
    #headers = {"Authorization": 'Bearer ' + access_token}    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    #print(headers)
    json_output = requests.get(endpoint, headers=headers).json()
    #return json_output
    #print(access_token)
    return json_output
    #print(json_output)



#api raw data output 
raw_data = apiCall(endpoint)
#print(raw_data)

#subscription data loop
for data in raw_data["value"]:
    subscription_info = {'displayName': data['displayName'], 'id': data['id'], 'tenantID': data['tenantId']}
    display_name = data["displayName"]
    print(subscription_info)