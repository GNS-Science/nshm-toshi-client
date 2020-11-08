"""
Test schema operations
"""

from io import BytesIO
from unittest import mock
from pathlib import Path

import unittest

import requests_mock

from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_client_base import clean_string

API_URL = "http://127.0.0.1:5000/graphql"
S3_URL = "https://nshm-tosh-api-test.s3.amazonaws.com/"


import json

class TestToshiFile(unittest.TestCase):

    def test_create_toshi_file_ok(self):
        with requests_mock.Mocker() as m:

            post_url = clean_string('{"acl": "public-read", "Content-MD5": "VXFQl5qqeuR/f4Yr4N0yQg=="}')

            query1_server_answer = '{"data":{"createFile":{"fileResult":{"postUrl":"%s"}}}}' % post_url

            m.post(API_URL, text=query1_server_answer)
            headers={"x-api-key":"THE_API_KEY"}
            myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

            filepath = Path(__file__)
            post_url = myapi.create_file(filepath)

            assert post_url["Content-MD5"] == "VXFQl5qqeuR/f4Yr4N0yQg=="

            history = m.request_history
            # print('HIST', history[0].text)
            assert history[0].url == API_URL
