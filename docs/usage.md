# Usage

To use ToshiClient.get_file in a project

```
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL
headers={"x-api-key":API_KEY}
api = ToshiFile(API_URL, None, None, headers=headers)

file = api.get_file('{example_id}')
```

Example response

```
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426
}
```

To use ToshiClient.get_file_detail in a project

```
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL
headers={"x-api-key":API_KEY}
api = ToshiFile(API_URL, None, None, headers=headers)

file = api.get_file_detail('{example_id}')
```
Example response

```
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426,
  'meta': {'mykey': 'myvalue', 'mykey2': 'myothervalue'}
}
```

To use ToshiClient.get_file_download_url in a project

```
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL
headers={"x-api-key":API_KEY}
api = ToshiFile(API_URL, None, None, headers=headers)

file = api.get_file_download_url('{example_id}')
```

Example response

```
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426,
  'file_url': 'https://s3.amazonaws.com/toshi-files/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip'
}
```