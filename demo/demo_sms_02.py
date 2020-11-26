import os
from nshm_toshi_client.strong_motion_station import StrongMotionStation


S3_URL = ""
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
API_KEY = "TOSHI_API_KEY_DEV"

headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":

    # initialise the api client
    toshi_sms_api = StrongMotionStation(API_URL, S3_URL,
        None, with_schema_validation=True, headers=headers)

    stations = toshi_sms_api.list()
    for row in stations:
        print( row )
