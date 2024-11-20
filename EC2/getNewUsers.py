import requests
import json

import pandas as pd
import numpy as np
from datetime import datetime
import pytz

import boto3
s3_client = boto3.client('s3')

# Get access token
def getToken():
    with open('~/signnow/keys.json', 'r') as jsonFile:
        myKeys = json.load(jsonFile)

    return myKeys['access_token']


def getUsers(page=1):
    access_token = getToken()
    url_member = 'https://api.signnow.com/v2/organizations/<organization_id>/members?page=' + str(page)

    header = {
        'Authorization' : 'bearer ' + access_token,
        'Content-type' : '',
        'Accept' : 'application/json'
    }

    resp_members = requests.request('GET', url_member, headers=header)
    data = resp_members.json()['data']
    meta = resp_members.json()['meta']

    lstUsers = data
    
    page = page + 1
    if page <= meta['pagination']['total_pages']:
        lstUsers.extend(getUsers(page))

    return lstUsers

if __name__ == '__main__':
    # List of emails that need to retrieve the documents from
    lst_email_to_extract = ['user1@gmail.com', 'user2@gmail.com']

    lstUsers = {"record" : getUsers()}

    new_timezone = pytz.timezone('US/Pacific')
    for i in lstUsers['record']:
        temp_last_login = i['last_login']
        if temp_last_login != None:
            for att1 in temp_last_login:
                i[att1] = temp_last_login[att1]

        for att2 in i['subscription']:
            i['subscription_' + att2] = i['subscription'][att2]
        del i['subscription']

        if i['last_login'] != None:
            i['last_login_datetime'] = datetime.fromtimestamp(i['last_login'], tz=new_timezone)
            i['created_at_datetime'] = datetime.fromtimestamp(i['created_at'], tz=new_timezone)
            
        if i['email'] in lst_email_to_extract:
            i['toExport'] = True
        else:
            i['toExport'] = False

    active_users = pd.DataFrame.from_records(lstUsers['record'])

    active_users.drop('user_agent', axis=1, inplace=True)
    active_users['last_login'] = active_users['last_login'].fillna(0).astype(int)
    active_users['last_login'] = active_users['last_login'].astype(int)
    active_users['created_at'] = active_users['created_at'].fillna(0).astype(int)
    active_users['created_at'] = active_users['created_at'].astype(int)

    today_ = '{:02d}'.format(datetime.now().year) + '{:02d}'.format(datetime.now().month) + '{:02d}'.format(datetime.now().day)
    active_users['dataloader'] = today_
    active_users.to_csv('~/signnow/users.csv', index=False)

    s3_client.upload_file('~/signnow/users.csv', 'Your-S3-bucket', 'database/user/users.csv')
