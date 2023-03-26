import adal
import requests 
import string
import json
import os
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

#standard Vars
keyname='sasecret'

#dictionaries
subscription_info = {}

def azureADApplicationConnect(client_ID,tenant_ID,client_secret):
    
    authentication_endpoint = "https://login.microsoftonline.com/"
    resource = "https://management.core.windows.net/"
    
    #connects using env vars to application
    context = adal.AuthenticationContext(authentication_endpoint + tenant_ID)
    token_response = context.acquire_token_with_client_credentials(resource,client_ID, client_secret)
    
    #get's access token
    access_token = token_response.get('accessToken')
    
    #return access token
    return access_token
    
    
def keyVaultConnect(keyvault_name,tenant_ID,client_ID,client_secret,keyname):
    #set's vars for KV connection & credentials
    KVUri = f"https://{keyvault_name}.vault.azure.net"
    credential = ClientSecretCredential(tenant_ID,client_ID,client_secret)
    client = SecretClient(vault_url=KVUri, credential=credential)
    sasecret=client.get_secret(keyname)

endpoint = f"https://management.azure.com/subscriptions?api-version=2020-01-01"

def apiCall(endpoint):
    access_token = azureADApplicationConnect(client_ID,tenant_ID,client_secret)
    headers = {"Authorization": 'Bearer ' + access_token}
    json_output = requests.get(endpoint, headers=headers).json()
    #return json_output
    #print(access_token)
    return json_output
    #print(json_output)

azureADApplicationConnect(client_ID,tenant_ID,client_secret)
#keyVaultConnect(keyvault_name,tenant_ID,client_ID,client_secret,keyname)
apiCall(endpoint)

#api raw data output 
raw_data = apiCall(endpoint)
#print(raw_data)

#subscription data loop
for data in raw_data["value"]:
    subscription_info = {'displayName': data['displayName'], 'id': data['id'], 'tenantID': data['tenantId']}
    #display_name = data["displayName"]
    print(subscription_info)