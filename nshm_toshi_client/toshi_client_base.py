from gql import gql, Client
from pathlib import Path
from gql.transport.requests import RequestsHTTPTransport
import logging
import json
import base64
import hashlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def clean_string(original_string):
    """
    Sanitise string, replacing illegal graphql chars with their escape sequences
    """
    return original_string\
        .encode('utf-8')\
        .replace(b"\\",  b"\\\\")\
        .replace(b"\"", b'\\\"')\
        .replace(b"\n", b"\\n")\
        .replace(b"\t", b"\\t")\
        .replace(b"\r", b"\\r")\
        .replace(b"\\x", b"\\\\x")\
        .decode('utf-8')

def attributes_as_str(attributes=None):
        attribs = attributes or []
        return str(attribs).replace("'key'", 'key').replace("'value'", 'value')\
            .replace("'", '"')\
            .replace('key: value', 'key: "value"')

class ToshiClientBase(object):

    def __init__(self, url, auth_token, with_schema_validation=True, headers=None ):
        """Summary

        Args:
          url (String): Toshi API service URL
          auth_token (String): JWT
          with_schema_validation (bool, optional): Validate client calls before dispatch
          headers (Dict, optional): custom headers (e.g. x-api-key)
        """
        if headers == None:
            headers = {"Authorization": "Bearer %s" % auth_token}

        transport = RequestsHTTPTransport(url=url, headers=headers, use_json=True)
        self._client = Client(transport=transport,
            fetch_schema_from_transport=with_schema_validation)
        self._with_schema_validation = with_schema_validation

    def run_query(self, query, variable_values=None):

        logger.debug('query: %s',  query)
        logger.debug('variable_values: %s',  variable_values)

        variable_values = variable_values or {}

        gql_query = gql(query)
        if self._with_schema_validation:
            self._client.validate(gql_query) #might throw graphql.error.base.GraphQLError

        response = self._client.execute(gql_query, variable_values)

        #logger.debug('response: %s', response)

        if response.get('errors') is None:
            return response
        else:
            logger.warning(response)
            return None