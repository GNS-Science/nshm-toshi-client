# from gql import gql
from hashlib import md5
import json
import base64
import requests

from .toshi_client_base import ToshiClientBase

class ToshiFile(ToshiClientBase):

    def __init__(self, url, s3_url, auth_token, with_schema_validation=True, headers=None ):
        super(ToshiFile, self).__init__(url, auth_token, with_schema_validation, headers)
        self._s3_url = s3_url

    def create_file(self, filepath):
        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: Int!) {
              createFile(
                  md5Digest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) {
                  ok
                  fileResult { id, fileName, fileSize, md5Digest, postUrl }
              }
            }'''

        filedata = open(filepath, 'rb')
        digest = base64.b64encode(md5(filedata.read()).digest()).decode()
        # print('DIGEST:', digest)

        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.close()
        # filedata.seek(0) #important!

        variables = dict(digest=digest, file_name=filepath.parts[-1], file_size=size)
        executed = self.run_query(qry, variables)

        #executed = self.client.execute(qry, variable_values=variables)
        # print(executed)
        pu = json.loads(executed['createFile']['fileResult']['postUrl'])
        return pu

    def upload_content(self, post_url, filepath):
        # print('POST DATA %s' % post_url )
        filedata = open(filepath, 'rb')
        files = {'file': filedata}
        response = requests.post(
            url=self._s3_url,
            data=post_url,
            files=files)
