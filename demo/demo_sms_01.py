import datetime as dt
import os
from pathlib import PurePath

from dateutil.tz import tzutc

from nshm_toshi_client.strong_motion_station import StrongMotionStation

S3_URL = ""  # ???
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
MAIN_XLS = "./data/Site_Metadata_Version1.0_(Kaiser_et_al_2017_BNZSEE).xlsx"

API_KEY = "TOSHI_API_KEY_DEV"
headers = {"x-api-key": os.getenv(API_KEY)}

if __name__ == "__main__":

    # initialise the api client
    toshi_sms_api = StrongMotionStation(API_URL, S3_URL, None, with_schema_validation=True, headers=headers)

    conf_file = PurePath('./README.md')

    toshi_sms_api.create(toshi_sms_api.get_example_create_variables())

    import xlrd

    workbook = xlrd.open_workbook(MAIN_XLS)
    thesheet = workbook.sheet_by_index(0)

    print("Rows: %s, Cols: %s" % (thesheet.nrows, thesheet.ncols))

    for row in [r for r in thesheet.get_rows()][6:]:
        vars = {
            "created": dt.datetime.now(tzutc()).isoformat(),
            "site_code": row[0].value,
            "site_class": row[1].value,
            "Vs30_mean": [
                row[2].value,
            ],
        }
        toshi_sms_api.create(vars)
        print(
            '.',
        )

    print("Done!")
