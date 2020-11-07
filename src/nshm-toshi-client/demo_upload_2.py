import base64
import json
import os
import requests

from gql import gql, Client, RequestsHTTPTransport, AIOHTTPTransport
from hashlib import md5
from pathlib import Path

API_URL = "https://qsz8j27tw6.execute-api.ap-southeast-2.amazonaws.com/test/graphql"
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"

API_KEY = "TOSHI_APIKEY_DEV"
#API_URL = 'http://127.0.0.1:5000/graphql'
S3_URL = "https://nshm-tosh-api-test.s3.amazonaws.com/"
S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/"

transport = RequestsHTTPTransport(url=API_URL, headers={"x-api-key":os.getenv(API_KEY)})

class DataFileClient():

    def __init__(self):
        self.client = Client(
  	        transport=transport,
  		      fetch_schema_from_transport=True
		    )

    def create_file(self, filepath):
        qry = gql('''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!) {
              createFile(
                  md5Digest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) {
                  ok
                  fileResult { id, fileName, fileSize, md5Digest, postUrl }
              }
            }''')

        filedata = open(filepath, 'rb')
        digest = base64.b64encode(md5(filedata.read()).digest()).decode()
        # print('DIGEST:', digest)

        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.close()
        # filedata.seek(0) #important!

        variables = dict(digest=digest, file_name=filepath.parts[-1], file_size=size)
        executed = self.client.execute(qry, variable_values=variables)
        # print(executed)
        pu = json.loads(executed['createFile']['fileResult']['postUrl'])
        return pu

    def upload_content(self, post_url, filepath):
        # print('POST DATA %s' % post_url )
        filedata = open(filepath, 'rb')
        files = {'file': filedata}
        response = requests.post(
          url=S3_URL,
          data=post_url,
          files=files)
        # print(dir(response))
        # print(response.status_code, response.text, response.reason)

if __name__ == "__main__":
    myapi = DataFileClient()
    filepath = Path("../opensha/nshm-nz-opensha/data/ruptureSets/CFM_SANSTVZ_5.1km_points_ddw2.zip")
    post_url = myapi.create_file(filepath)
    print("uploading ", filepath.parts[-1])
    myapi.upload_content(post_url, filepath)
    print('Done')