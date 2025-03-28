Easy to set up and use - if you don't use custom queries.
it's only at version 0.14.0
Required to generate client:
- schema, queries, existing queries work verbatim
- minimal config:
```
[tool.ariadne-codegen]
schema_path = "schema.graphql"
queries_path = "queries.graphql"
enable_custom_operations = true
```
- poetry run ariadne-codegen
- ran into problems with FileInterface. Needed to add `id` to it.
- using queries is easy, returns typed result

```python
async def get_file():
    client = Client(
        url= env['VITE_GRAPHQL_ENDPOINT'], 
        headers={"X-API-KEY": env['VITE_GRAPHQL_API_KEY']}
    )

    response = await client.file_details_query(id="SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwODMzOQ==")

    print(response)

    print(response.node.id)
    print(response.node.source_solution.typename__)
```


poetry run python3 -c "from spike_ariadne_codegen import try_it; try_it()"


- Can build custom queries dynamically (if enabled in config at codegen time).
- This was painful, and I could not get it going 100%

poetry run python3 -c "from spike_ariadne_codegen import try_custom; try_custom()"

- Can create new json from scratch with generated classes, might be clunky when it comes to things like __typename