"""Ensure that gql arguments are being handled."""

import json

import requests_mock

from nshm_toshi_client.toshi_client_base import ToshiClientBase

API_URL = "http://fake_api/graphql"
S3_URL = "https://some-tosh-api.com/"


def test_query_without_args():
    with requests_mock.Mocker() as m:

        query = 'query {about}'
        server_response = '{"data":{"about": "hello world"}}'
        m.post(API_URL, text=server_response)
        headers = {"x-api-key": "THE_API_KEY"}
        myapi = ToshiClientBase(API_URL, None, with_schema_validation=False, headers=headers)

        response = myapi.run_query(query, variable_values=None)
        history = m.request_history
        assert response == json.loads(server_response)['data']
        assert history[0].url == API_URL


def test_query_with_args():
    with requests_mock.Mocker() as m:

        query = """
            query getContinentName ($code: ID!) {
                continent (code: $code) {
                    name
                }
            }
        """
        server_response = '{"data":{"continent": "Africa"}}'
        m.post(API_URL, text=server_response)
        headers = {"x-api-key": "THE_API_KEY"}
        myapi = ToshiClientBase(API_URL, None, with_schema_validation=False, headers=headers)

        response = myapi.run_query(query, variable_values={"code": "AF"})
        history = m.request_history
        assert response == json.loads(server_response)['data']
        assert history[0].url == API_URL
        assert '"variables": {"code": "AF"}' in history[0].text
