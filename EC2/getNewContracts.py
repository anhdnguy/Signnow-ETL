import requests
import json
import io

import string
import unicodedata

import time
from datetime import datetime, timedelta
import pytz

import pandas as pd

import boto3
s3_client = boto3.client('s3')

# Get access token
def getToken():
    with open('~/signnow/keys.json', 'r') as jsonFile:
        myKeys = json.load(jsonFile)

    return myKeys['access_token']


# Making sure the file name is valid and only limit 60 characters
def format_filename(topic):
    valid_filename_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    invalid = '<>:"/\|?*. '
    for char in invalid:
        topic = topic.replace(char, '_')

    cleaned_filename = unicodedata.normalize('NFKD', topic).encode('ASCII', 'ignore').decode()
    cleaned_filename = ''.join(c for i, c in enumerate(cleaned_filename) if c in valid_filename_chars and i <= 60)

    return '{}'.format(cleaned_filename)


# Pause the program to meet with the 500 calls threshold
def sleep_(reset_):
    reset_stamp = datetime.fromtimestamp(int(reset_))
    now_ = datetime.now()
    diff_sec = reset_stamp - now_
    time_sleep = diff_sec.seconds - 3590
    print(f'sleep for {time_sleep}')
    time.sleep(time_sleep)


# Download file content
def download_blob (doc_id):
    access_token = getToken()
    header = {
        'Authorization' : 'bearer ' + access_token,
        'Content-type' : '',
        'Accept' : 'application/json'
    }
    params = {
        'type' : 'collapsed',
        'with_history' : 1
    }
    try: 
        url = f'https://api.signnow.com/document/{doc_id}/download'
        doc_data = requests.request('GET', url, headers=header, params=params)
        doc_content = doc_data.content
        return doc_content
    except Exception as e:
        print(f'download {doc_id} failed: {e}')
        return f'None'


# Upload the file to S3
def upload_S3(PDF_STREAM, S3_KEY):
    BUCKET_NAME = 'Your-S3-bucket'
    try:
        s3_client.upload_fileobj(PDF_STREAM, BUCKET_NAME, S3_KEY, ExtraArgs={'ContentType': 'application/pdf'})
        print(f"File uploaded successfully to s3://{BUCKET_NAME}/{S3_KEY}")
    except FileNotFoundError:
        print(f"The file '{S3_KEY}' was not found")
    except Exception as e:
        print(f"An error occurred: {e}")


# Search for documents within a given timeframe and get the information
def search_doc (email, diff=timedelta(days=1), end_=datetime.now(pytz.timezone('US/Pacific')), page=1):
    start_ = end_ - diff
    per_page = '30'
    new_timezone = pytz.timezone('US/Pacific')
    access_token = getToken()
    header = {
        'Authorization' : 'bearer ' + access_token,
        'Content-type' : '',
        'Accept' : 'application/json'
    }
    url = 'https://api.signnow.com/v2/organizations/<organization_id>/documents/search' + \
        '?sort[changed]=desc&filters=[{\"owner\":{\"type\": \"=\", \"value\":\"' + email + '\"}},' + \
            '{\"status\":{\"type\": \"=\", \"value\":\"signed\"}}]&per_page=' + per_page + '&page=' + str(page)
    
    try:
        response = requests.request('GET', url, headers=header)
        data = response.json()['data']
        meta = response.json()['meta']
    except Exception as e:
        print(f'error getting doc from {email}, page: {page}:\n {e}')

    # Check if the remaining call is low and pause the program until it is refreshed
    if response.headers.get('X-RateLimit-Remaining') == '3':
        sleep_(data.headers.get('X-RateLimit-Reset'))

    filtered_data = []
    for x in data:
        signned_date = datetime.fromtimestamp(int(x['updated']), tz=new_timezone)
        if start_ < signned_date < end_:
            doc_content = download_blob(x['id'])
            # Create an in-memory stream using BytesIO
            pdf_stream = io.BytesIO(doc_content)
            doc_updated = signned_date.strftime('%m-%d-%YT%H-%M-%S')
            doc_name = format_filename(x['document_name']) + '.pdf'
            S3_KEY = 'contracts/' + x['owner'] + '/' + doc_updated + '/' + doc_name
            upload_S3(pdf_stream, S3_KEY)
            # Explicitly close the stream to release memory
            pdf_stream.close()
            sub_data = {
                'id' : x['id'],
                'owner_id' : x['user_id'],
                'document_name' : x['document_name'],
                'created' : datetime.fromtimestamp(int(x['created']), tz=new_timezone).strftime('%m-%d-%Y %H:%M:%S'),
                'updated' : signned_date.strftime('%m-%d-%Y %H:%M:%S'),
                'original_filename' : x['original_filename'],
                's3_id' : S3_KEY
            }
            filtered_data.append(sub_data)
        else:
            return filtered_data

    page += 1
    if page <= meta['pagination']['total_pages']:
        filtered_data.extend(search_doc (email, page))

    return filtered_data


if __name__ == '__main__':
    diff = timedelta(days=7)
    filtered_json = []

    lstUsers = pd.read_csv('~/signnow/users.csv')
    userstoExport = lstUsers[lstUsers['toExport']]
    userstoExportlist = userstoExport['email'].tolist()

    for user in userstoExportlist:
        filtered_json.extend(search_doc(user, diff))
        # filtered_json.extend(search_doc(user))
    
    with open('~/signnow/documents.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_json, f, ensure_ascii=False, indent=4)
    
    today_ = '{:02d}'.format(datetime.now().year) + '{:02d}'.format(datetime.now().month) + '{:02d}'.format(datetime.now().day)
    s3_client.upload_file('~/signnow/documents.json', 'Your-S3-bucket',
                          'database/document/dataloader=' + today_ + '/documents.json')
    