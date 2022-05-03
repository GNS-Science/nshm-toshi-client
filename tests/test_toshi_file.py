"""
Test schema operations
"""

import json
from io import BytesIO
from unittest import mock
from pathlib import Path

import unittest

import requests_mock

from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_client_base import clean_string

API_URL = "http://fake_api/graphql"
S3_URL = "https://some-tosh-api.com/"


class TestToshiFile(unittest.TestCase):
    def test_create_toshi_file_ok(self):
        with requests_mock.Mocker() as m:

            post_url = clean_string('{"acl": "public-read", "Content-MD5": "VXFQl5qqeuR/f4Yr4N0yQg=="}')

            query1_server_answer = '{"data":{"create_file":{"file_result":{"id":"ABCD","post_url":"%s"}}}}' % post_url

            m.post(API_URL, text=query1_server_answer)
            headers = {"x-api-key": "THE_API_KEY"}
            myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

            filepath = Path(__file__)
            _id, post_url = myapi.create_file(filepath)

            assert post_url["Content-MD5"] == "VXFQl5qqeuR/f4Yr4N0yQg=="

            history = m.request_history
            # print('HIST', history[0].text)
            assert history[0].url == API_URL

    def test_create_toshi_file_with_meta_ok(self):
        with requests_mock.Mocker() as m:

            post_url = clean_string('{"acl": "public-read", "Content-MD5": "VXFQl5qqeuR/f4Yr4N0yQg=="}')

            query1_server_answer = '{"data":{"create_file":{"file_result":{"id":"ABCD","post_url":"%s"}}}}' % post_url

            m.post(API_URL, text=query1_server_answer)
            headers = {"x-api-key": "THE_API_KEY"}
            myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

            meta = dict(mykey="myvalue", mykey2='myothervalue')

            filepath = Path(__file__)
            _id, post_url = myapi.create_file(filepath, meta)

            assert post_url["Content-MD5"] == "VXFQl5qqeuR/f4Yr4N0yQg=="

            history = m.request_history
            # print('HIST', history[0].text)
            assert history[0].url == API_URL

    def test_get_file_ok(self):
        with requests_mock.Mocker() as m:

            query1_server_answer = '''{
                "data": {
                    "node": {
                        "__typename": "InversionSolutionNrml",
                        "id": "SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==",
                        "file_name": "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip",
                        "file_size": 3331426,
                        "meta": {"mykey":"myvalue","mykey2":"myothervalue"}
                    }
                }
            }'''

            m.post(API_URL, text=query1_server_answer)
            headers = {"x-api-key": "THE_API_KEY"}
            myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

            file_detail = myapi.get_file("SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==")

            assert file_detail["id"] == "SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw=="
            assert file_detail["file_name"] == "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip"
            assert file_detail["file_size"] == 3331426
            assert file_detail["meta"] == {"mykey": "myvalue", "mykey2": "myothervalue"}

    def test_get_file_dowload_url_ok(self):
        with requests_mock.Mocker() as m:

            query1_server_answer = '''{
                "data": {
                    "node": {
                        "__typename": "InversionSolutionNrml",
                        "id": "SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==",
                        "file_name": "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip",
                        "file_size": 3331426,
                        "meta": {"mykey":"myvalue","mykey2":"myothervalue"},
                        "file_url": "https://s3.amazonaws.com/toshi-files/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip"
                    }
                }
            }'''

            m.post(API_URL, text=query1_server_answer)
            headers = {"x-api-key": "THE_API_KEY"}
            myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

            file_detail = myapi.get_file("SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==", True)

            assert file_detail["id"] == "SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw=="
            assert file_detail["file_name"] == "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip"
            assert file_detail["file_size"] == 3331426
            assert file_detail["meta"] == {"mykey": "myvalue", "mykey2": "myothervalue"}
            assert (
                file_detail["file_url"]
                == "https://s3.amazonaws.com/toshi-files/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip"
            )
