## */30 * * * * ~/anaconda3/envs/wu_signnow/bin/python ~/signnow/refresh.py

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
basic = os.getenv('basic')
username = os.getenv('username')
password = os.getenv('password')

with open('~/signnow/keys.json', 'r') as jsonFile:
    myKeys = json.load(jsonFile)
    
header = {
    'Authorization' : 'Basic ' + basic
}

body = {
    'grant_type' : 'refresh_token',
    'refresh_token' : myKeys['refresh_token'],
    'expiration_time' : '3600'
}

url = 'https://api.signnow.com/oauth2/token'

response = requests.post(url=url, headers=header, data=body)
response.close()
    
myKeys['access_token'] = response.json()['access_token']
myKeys['refresh_token'] = response.json()['refresh_token']
jsonFile = open('~/signnow/keys.json', 'w+')
jsonFile.write(json.dumps(myKeys))
jsonFile.close()

## Initial run
# header = {
#     'Authorization' : 'Basic ' + basic
# }

# body = {
#     'username' : username,
#     'password' : password,
#     'grant_type' : 'password',
#     'expiration_time' : '3600',
#     'scope' : '*'
# }

# url = 'https://api.signnow.com/oauth2/token'

# response = requests.post(url=url, headers=header, data=body)
# response.close()

# with open('keys.json', 'r') as jsonFile:
#     myKeys = json.load(jsonFile)
# myKeys['access_token'] = response.json()['access_token']
# myKeys['refresh_token'] = response.json()['refresh_token']
# jsonFile = open('keys.json', 'w+')
# jsonFile.write(json.dumps(myKeys))
# jsonFile.close()