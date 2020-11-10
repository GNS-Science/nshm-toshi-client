
import os
import datetime as dt
from dateutil.tz import tzutc
from nshm_toshi_client.rupture_generation_task import RuptureGenerationTask

S3_URL = "https://nshm-tosh-api-dev.s3.amazonaws.com/"
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
API_KEY = "TOSHI_API_KEY_DEV"
headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":


    # initialise the api client
    ruptgen_api = RuptureGenerationTask(API_URL, S3_URL,
        None, with_schema_validation=True, headers=headers)

    config_file_id = ruptgen_api.upload_file(__file__)

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

    #link task to the input file
    ruptgen_api.link_task_file(task_id, config_file_id, 'READ')

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
    ruptgen_api.upload_task_file(task_id, __file__, 'WRITE') #one of WRITE, READ. READ_WRITE
    print('Done')
