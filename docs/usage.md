# Usage

## Setup

Required env variables:

```
NZSHM22_TOSHI_API_URL=https://example-api-url.com
NZSHM22_TOSHI_API_KEY=example-api-key
NZSHM22_TOSHI_S3_URL=https://example-s3-url.com
```

contact @chrisbc for real urls/keys

## Methods

To use ToshiFile.get_file in a project

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
  'file_size': 3331426,
  'meta': {'mykey': 'myvalue', 'mykey2': 'myothervalue'}
}
```

To use ToshiClient.get_file and get file_url in a project

```
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL
headers={"x-api-key":API_KEY}
api = ToshiFile(API_URL, None, None, headers=headers)

file = api.get_file_download_url('{example_id}', true)
```

Example response

```
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426,
  'meta': {'mykey': 'myvalue', 'mykey2': 'myothervalue'},
  'file_url': 'https://s3.amazonaws.com/toshi-files/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip'
}
```

To use ToshiClient.download_file in a project

```
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL
headers={"x-api-key":API_KEY}
api = ToshiFile(API_URL, None, None, headers=headers)

example_file_path = 'usr/tmp'
api.download_file('{example_id}', example_file_path)
```

If successful, prints:

```
saving to usr/tmp/{example_id}
````

If failure, prints:

```
Download failed: status code {status_code} (eg. 404)
```
