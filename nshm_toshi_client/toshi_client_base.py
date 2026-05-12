import logging

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from nshm_toshi_client.auth import CREDENTIALS_PATH, ToshiCredentialAuth, ToshiM2MAuth, ToshiTokenManager
from nshm_toshi_client.config import (
    COGNITO_CLIENT_ID,
    COGNITO_CLIENT_SECRET,
    COGNITO_DOMAIN,
    COGNITO_SCIENTIST_CLIENT_ID,
)

logger = logging.getLogger(__name__)


def clean_string(original_string):
    """
    Sanitise string, replacing illegal graphql chars with their escape sequences
    """
    return (
        original_string.encode('utf-8')
        .replace(b"\\", b"\\\\")
        .replace(b"\"", b'\\"')
        .replace(b"\n", b"\\n")
        .replace(b"\t", b"\\t")
        .replace(b"\r", b"\\r")
        .replace(b"\\x", b"\\\\x")
        .decode('utf-8')
    )


def attributes_as_str(attributes=None):
    attribs = attributes or []
    return (
        str(attribs)
        .replace("'key'", 'key')
        .replace("'value'", 'value')
        .replace("'", '"')
        .replace('key: value', 'key: "value"')
    )


def kvl_to_graphql(field_name, kvl_as_dict):
    assert isinstance(kvl_as_dict, dict)
    value = f"{field_name}: [\n"
    for k, v in kvl_as_dict.items():
        value += f'{{k: "{k}" v: "{v}" }}\n'
    value += "]"
    return value


class ToshiClientBase:
    def __init__(
        self,
        url,
        auth_token=None,
        with_schema_validation=True,
        headers=None,
        retries=6,
        timeout=None,
        token_manager: ToshiTokenManager | None = None,
    ):
        """Summary

        Args:
          url (String): Toshi API service URL
          auth_token (String): JWT (static; use token_manager for long-running jobs)
          with_schema_validation (bool, optional): Validate client calls before dispatch
          headers (Dict, optional): custom headers (e.g. x-api-key)
          token_manager (ToshiTokenManager, optional): explicit M2M token manager; if omitted
            and NZSHM22_TOSHI_COGNITO_* env vars are set, one is created automatically
        """
        if token_manager is None and COGNITO_CLIENT_ID and COGNITO_CLIENT_SECRET and COGNITO_DOMAIN:
            if auth_token is not None:
                logger.warning(
                    "ToshiClientBase: explicit auth_token ignored — NZSHM22_TOSHI_COGNITO_* env vars "
                    "are set, so M2M auth is being used instead. Unset the env vars or pass "
                    "token_manager=... to override."
                )
            logger.debug("ToshiClientBase: auto-configuring M2M token manager from env vars")
            token_manager = ToshiTokenManager(COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_DOMAIN)

        if token_manager is not None:
            transport = RequestsHTTPTransport(
                url=url, auth=ToshiM2MAuth(token_manager), use_json=True, retries=retries, timeout=timeout
            )
        elif CREDENTIALS_PATH.exists() and COGNITO_DOMAIN and COGNITO_SCIENTIST_CLIENT_ID:
            if auth_token is not None:
                logger.warning(
                    "ToshiClientBase: explicit auth_token ignored — ~/.toshi/credentials exists, "
                    "so interactive auth is being used instead. Run `toshi-auth logout` or pass "
                    "headers=... to override."
                )
            logger.debug("ToshiClientBase: auto-configuring interactive auth from ~/.toshi/credentials")
            auth = ToshiCredentialAuth(COGNITO_DOMAIN, COGNITO_SCIENTIST_CLIENT_ID)
            transport = RequestsHTTPTransport(url=url, auth=auth, use_json=True, retries=retries, timeout=timeout)
        else:
            if headers is None:
                if auth_token is None:
                    raise ValueError(
                        "No auth configured. Provide one of: "
                        "token_manager, NZSHM22_TOSHI_COGNITO_* env vars, "
                        "~/.toshi/credentials (toshi-auth login), "
                        "auth_token=..., or custom headers=..."
                    )
                headers = {"Authorization": f"Bearer {auth_token}"}
            transport = RequestsHTTPTransport(url=url, headers=headers, use_json=True, retries=retries, timeout=timeout)

        self._client = Client(transport=transport, fetch_schema_from_transport=with_schema_validation)
        self._with_schema_validation = with_schema_validation

    def run_query(self, query, variable_values=None):

        logger.debug('query: %s', query)
        logger.debug('variable_values: %s', variable_values)

        gql_query = gql(query)
        # TODO: started asserting after update to v3.0+ gql
        # if self._with_schema_validation:
        #     self._client.validate(gql_query)  # might throw graphql.error.base.GraphQLError

        gql_query.variable_values = variable_values or {}
        response = self._client.execute(gql_query)

        # logger.debug('response: %s', response)

        if response.get('errors') is None:
            return response
        else:
            logger.warning(response)
            return None
