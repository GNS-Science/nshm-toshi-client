import asyncio
from graphql_client import Client
from dotenv import dotenv_values

from graphql_client.exceptions import GraphQLClientGraphQLError, GraphQLClientGraphQLMultiError

env = dotenv_values(".env")

async def get_subtask_files():
    try:
        client = Client(
            url= env['VITE_GRAPHQL_ENDPOINT'], 
            headers={"X-API-KEY": env['VITE_GRAPHQL_API_KEY']}
        )

        # prod
        # response = await client.one_general(id="R2VuZXJhbFRhc2s6MTAzNzIz")
        # test
        # response = await client.one_general(id="R2VuZXJhbFRhc2s6MTAxNTk1")
        response = await client.one_general(id="R2VuZXJhbFRhc2s6MTAzNzIz")

        print(response.model_dump_json(indent=2))
    except GraphQLClientGraphQLMultiError as e:
        print(e)
        print(e.errors[0])

def get_subtask_files_sync():
    asyncio.run(get_subtask_files())

async def create_task():
    try:
        client = Client(
            url= env['VITE_GRAPHQL_ENDPOINT'], 
            headers={"X-API-KEY": env['VITE_GRAPHQL_API_KEY']}
        )

        response = await client.create_general_task(created="2022-06-09T08:07:44.006744+00:00", agent_name="oakley", title="testing the API", description="a test")

        print(response.model_dump_json(indent=2))
    except Exception as e:
        print (e)

def create_task_sync():
    asyncio.run(create_task())