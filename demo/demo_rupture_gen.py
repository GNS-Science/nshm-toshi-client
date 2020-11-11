
import os
import datetime as dt
from dateutil.tz import tzutc
from nshm_toshi_client.rupture_generation_task import RuptureGenerationTask
from pathlib import PurePath

import logging

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/"
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"

# uncomment for local S3 testing
# API_URL = 'http://127.0.0.1:5000/graphql'
# S3_URL = "http://localhost:4569"

API_KEY = "TOSHI_API_KEY_DEV"
headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":


    # initialise the api client
    ruptgen_api = RuptureGenerationTask(API_URL, S3_URL,
        None, with_schema_validation=True, headers=headers)

    conf_file = PurePath('./README.md')

    conf_id = ruptgen_api.upload_file(conf_file) #one of WRITE, READ. READ_WRITE

    # set the task_'create' values
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


    #create the new task, when the task starts (or when scheduledd)
    task_id = ruptgen_api.create_task(create_args)

    ruptgen_api.link_task_file(task_id, conf_id, 'READ')

    ##
    # imagine some task work is done now
    ##

    # set the task 'complete' values
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
    ruptgen_api.complete_task(done_args) #update the task with successful results

    #upload some task output file
    print('ruptgen_api.complete_task(done_args)')
    ruptgen_api.upload_task_file(task_id, __file__, 'WRITE') #one of WRITE, READ. READ_WRITE
    print('Done')
