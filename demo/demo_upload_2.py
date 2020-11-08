
import os
from pathlib import Path
from nshm_toshi_client.toshi_file import ToshiFile
API_URL = "https://qsz8j27tw6.execute-api.ap-southeast-2.amazonaws.com/test/graphql"
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"

API_KEY = "TOSHI_APIKEY_DEV"
#API_URL = 'http://127.0.0.1:5000/graphql'
S3_URL = "https://nshm-tosh-api-test.s3.amazonaws.com/"
S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/"

headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":
    myapi = ToshiFile(API_URL, S3_URL, None, with_schema_validation=True, headers=headers)
    filepath = Path("../opensha/nshm-nz-opensha/data/ruptureSets/CFM_SANSTVZ_5.1km_points_ddw2.zip")
    post_url = myapi.create_file(filepath)
    print('POST', post_url)
    print("uploading ", filepath.parts[-1])
    myapi.upload_content(post_url, filepath)
    print('Done')