# from gql import gql
import base64
import json
import logging
import os
from hashlib import md5

import requests
from urllib3.util import Retry

from .timeout_http_adapter import TimeoutHTTPAdapter
from .toshi_client_base import ToshiClientBase, kvl_to_graphql

# import http


# see https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
session = requests.Session()
# http.client.HTTPConnection.debuglevel = 1 #prints some header

# this is for our file upload
retry_strategy = Retry(
    total=6,
    backoff_factor=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
)

# Mount it for both http and https usage
adapter = TimeoutHTTPAdapter(timeout=2.5, max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

log = logging.getLogger(__name__)


class ToshiFile(ToshiClientBase):
    def __init__(self, url, s3_url, auth_token, with_schema_validation=True, headers=None):
        super(ToshiFile, self).__init__(url, auth_token, with_schema_validation, headers)
        self._s3_url = s3_url

    def create_file(self, filepath, meta=None):
        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!) {
              create_file(
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size

                  ##META##

              ) {
                  ok
                  file_result { id, file_name, file_size, md5_digest, post_url, meta {k v}}
              }
            }'''

        if meta:
            qry = qry.replace("##META##", kvl_to_graphql('meta', meta))

        print(qry)

        filedata = open(filepath, 'rb')
        digest = base64.b64encode(md5(filedata.read()).digest()).decode()
        # print('DIGEST:', digest)

        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.close()

        variables = dict(digest=digest, file_name=filepath.parts[-1], file_size=size)
        executed = self.run_query(qry, variables)

        print("executed", executed)
        post_url = json.loads(executed['create_file']['file_result']['post_url'])
        return (executed['create_file']['file_result']['id'], post_url)

    def upload_content(self, post_url, filepath):
        log.debug(f'upload_content() POST URL: {post_url}; PATH: {filepath}')
        filedata = open(filepath, 'rb')
        files = {'file': filedata}
        log.debug(f'upload_content() _s3_url: {self._s3_url}')

        response = requests.post(url=self._s3_url, data=post_url, files=files)
        log.debug(f'response {response}')
        response.raise_for_status()

    def upload_content_v2(self, post_url: str, post_data: dict, filepath: str | os.PathLike):
        """Upload a blob to S3.

        Args:
            post_url: The URL to post a file to S3.
            post_data: The data to post a file to S3.
            filepath: The path to the file to upload.
        """
        log.debug(f'upload_content() POST URL: {post_url}; PATH: {filepath}')
        filedata = open(filepath, 'rb')
        files = {'file': filedata}
        log.debug(f'upload_content() _s3_url: {self._s3_url}')

        response = requests.post(url=self._s3_url, data=post_data, files=files)
        log.debug(f'response {response}')
        response.raise_for_status()

    def get_download_url(self, id):
        qry = '''
        query download_file ($id:ID!) {
                node(id: $id) {
            __typename
            ... on File {
              file_name
              file_size
              file_url
            }
          }
        }'''

        print(qry)
        input_variables = dict(id=id)
        executed = self.run_query(qry, input_variables)
        return executed['node']

    def get_file(self, id, with_file_url: bool = False):
        qry = '''
        query file ($id:ID!) {
                node(id: $id) {
            __typename
            ... on Node {
              id
            }
            ... on FileInterface {
              file_name
              file_size
              meta {k v}

             #FILE_URL

            }
          }
        }'''
        if with_file_url:
            qry = qry.replace("#FILE_URL", "file_url")

        # print(qry)
        input_variables = dict(id=id)
        executed = self.run_query(qry, input_variables)
        return executed['node']

    def download_file(self, id, target_dir, target_name=None):
        qry = '''
        query file ($id:ID!) {
                node(id: $id) {
            __typename
            ... on Node {
              id
            }
            ... on FileInterface {
              file_name
              file_url
            }
          }
        }'''

        # print(qry)
        input_variables = dict(id=id)
        executed = self.run_query(qry, input_variables)
        url = executed['node']['file_url']
        filename = target_name if target_name else executed['node']['file_name']

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        file_path = os.path.join(target_dir, filename)

        r = requests.get(url, stream=True)
        if r.ok:
            with open(file_path, 'wb') as f:
                f.write(r.content)
            return file_path
        else:
            raise (RuntimeError(f'Error downloading file {filename}: Status code {r.status_code}'))
