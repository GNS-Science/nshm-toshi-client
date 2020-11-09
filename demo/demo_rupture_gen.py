
import os
import datetime as dt
from dateutil.tz import tzutc
from nshm_toshi_client.rupture_generation_task import RuptureGenerationTask

S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/"
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
API_KEY = "TOSHI_API_KEY_DEV"

headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":
    ruptgen_api = RuptureGenerationTask(API_URL, S3_URL, None, with_schema_validation=True, headers=headers)

    # create keys
    #['started', 'permutationStrategy', 'openshaCore', 'openshaCommons', 'openshaUcerf3', 'nshmNzOpensha', 'maxJumpDistance', 'maxSubSectionLength', 'maxCumulativeAzimuth', 'minSubSectionsPerParent']
    create_args = {
     'started':dt.datetime.now(tzutc()).isoformat(),
     'permutationStrategy': 'UCERF3',
     'openshaCore': "A",
     'openshaCommons': "B",
     'openshaUcerf3': "C",
     'nshmNzOpensha': "D",
     'maxJumpDistance':5.0,
     'maxSubSectionLength':0.5,
     'maxCumulativeAzimuth':580.0,
     'minSubSectionsPerParent':2
    }

    #create result
    task_id = ruptgen_api.create_task(create_args)
    print("Created new task:", task_id)

    # complete keys
    #['taskId', 'duration', 'result', 'state', 'ruptureCount', 'subsectionCount', 'clusterConnectionCount'])
    done_args = {
     'taskId':task_id,
     'duration':45.45,
     'result':"SUCCESS",
     'state':"DONE",
     'ruptureCount': 505,
     'subsectionCount':55,
     'clusterConnectionCount':23
    }

    #update task result
    ruptgen_api.complete_task(done_args)

    #upload some task file
    ruptgen_api.upload_task_file(task_id, __file__)
    print('Done')

