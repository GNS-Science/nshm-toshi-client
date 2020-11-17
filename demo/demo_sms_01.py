
import os
import datetime as dt
from dateutil.tz import tzutc
from nshm_toshi_client.strong_motion_station import StrongMotionStation
from pathlib import PurePath

import logging

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


S3_URL = "" #REMOVE THIS !!
API_URL = "https://k6lrxgwqj9.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"


MAIN_XLS = "./data/Site_Metadata_Version1.0_(Kaiser_et_al_2017_BNZSEE).xlsx"

# uncomment for local S3 testing
# API_URL = 'http://127.0.0.1:5000/graphql'
# S3_URL = "http://localhost:4569"

API_KEY = "TOSHI_API_KEY_DEV"
headers={"x-api-key":os.getenv(API_KEY)}

if __name__ == "__main__":


    # initialise the api client
    toshi_sms_api = StrongMotionStation(API_URL, S3_URL,
        None, with_schema_validation=True, headers=headers)

    conf_file = PurePath('./README.md')


    toshi_sms_api.create(toshi_sms_api.get_example_create_variables())

    import xlrd
    import datetime as dt


    workbook = xlrd.open_workbook(MAIN_XLS)
    thesheet = workbook.sheet_by_index(0)

    print("Rows: %s, Cols: %s" % (thesheet.nrows, thesheet.ncols))

    i = 0
    for row in [r for r in thesheet.get_rows()][6:12]:
        # print(i, row )
        vars = { "created": dt.datetime.now(tzutc()).isoformat(),
            "site_code": row[0].value,
            "site_class": row[1].value,
            "Vs30_mean": [row[2].value,]}
        toshi_sms_api.create(vars)
        i+=1

    """
    5 [text:'Station', text:'Site Class', text:'Vs30', text:'Tsite', text:'Zb', text:'Q_Vs30', text:'Q_Tsite', text:'D_Tsite', text:'Q_Zb', text:'References ', empty:'', empty:'', empty:'', empty:'', empty:'', empty:'', empty:'']
    6 [text:'014A', text:'E', number:150.0, number:1.25, number:110.0, text:'Q2', text:'Q3', text:'I', text:'Q3', text:'McVerry 2011', number:0.0, number:0.0, number:0.0, number:0.0, number:0.0, number:0.0, number:0.0]
    7 [text:'015A', text:'B', number:1000.0, text:'<0.1', number:0.0, text:'Q3', text:'Q3', text:'I', text:'Q3', text:'Perrin et al. 2015', number:0.0, number:0.0, number:0.0, number:0.0, number:0.0, number:0.0, number:0.0]
    """

    # for crange in thesheet.col_label_ranges:
    #     rlo, rhi, clo, chi = crange
    #     for rx in xrange(rlo, rhi):
    #         for cx in xrange(clo, chi):
    #             print("Column label at (rowx=%d, colx=%d) is %r" % (rx, cx, thesheet.cell_value(rx, cx)))


    #conf_id = toshi_api.upload_file(conf_file) #one of WRITE, READ. READ_WRITE


    """
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
    task_id = toshi_api.create_task(create_args)

    toshi_api.link_task_file(task_id, conf_id, 'READ')

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
    toshi_api.complete_task(done_args) #update the task with successful results

    #upload some task output file
    print('toshi_api.complete_task(done_args)')
    toshi_api.upload_task_file(task_id, __file__, 'WRITE') #one of WRITE, READ. READ_WRITE
    print('Done')
    """