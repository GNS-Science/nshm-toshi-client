import asyncio
from graphql_client import Client
from graphql_client.custom_queries import Query
from graphql_client.custom_fields import (
    FileInterfaceInterface,
    NodeInterface,
    InversionSolutionNrmlFields,
    AggregateInversionSolutionFields,
    InversionSolutionFields,
    ScaledInversionSolutionFields,
    TimeDependentInversionSolutionFields,
)

from dotenv import dotenv_values

from graphql_client.file_details_query import FileDetailsQuery, FileDetailsQueryNodeNode

env = dotenv_values(".env")


async def get_file():
    client = Client(
        url= env['VITE_GRAPHQL_ENDPOINT'], 
        headers={"X-API-KEY": env['VITE_GRAPHQL_API_KEY']}
    )

    response = await client.file_details_query(id="SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwODMzOQ==")

    print(response.model_dump_json(indent=2))

    print(response.node.id)
    print(response.node.source_solution.typename__)

def try_it():
    asyncio.run(get_file())

def make_response():
    print("hello")
    node = FileDetailsQueryNodeNode(__typename="File", id="hello")
    response = FileDetailsQuery(node=node)
    print(response)
    print (response.model_dump_json(indent=2))

async def get_custom():

    client = Client(
        url= env['VITE_GRAPHQL_ENDPOINT'], 
        headers={"X-API-KEY": env['VITE_GRAPHQL_API_KEY']}
    )

    my_query = Query.node(id="SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwODMzOQ==").fields(
        NodeInterface.id,
    ).on("FileInterface", 
         FileInterfaceInterface.file_name,
         FileInterfaceInterface.file_size,
         FileInterfaceInterface.meta().fields(
             FileInterfaceInterface.meta().k,
             FileInterfaceInterface.meta().v
         )).on("InversionSolutionNrml",
               InversionSolutionNrmlFields.created,
               InversionSolutionNrmlFields.source_solution.on(
                   "AggregateInversionSolution", AggregateInversionSolutionFields.id
               )).on("InversionSolution", InversionSolutionFields.id
                ).on("ScaledInversionSolution", ScaledInversionSolutionFields.id
                ).on("TimeDependentInversionSolution", TimeDependentInversionSolutionFields.id)
               

    response = await client.query(my_query, operation_name="node")

    print(response)

def try_custom():
    asyncio.run(get_custom())

if __name__ == '__main__':
    try_it()
