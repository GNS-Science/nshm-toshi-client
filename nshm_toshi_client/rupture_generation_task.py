# from gql import gql
from hashlib import md5
import json
import base64
import requests
from pathlib import PurePath

from .toshi_client_base import ToshiClientBase
from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_task_file import ToshiTaskFile
#from .toshi_file import ToshiFile

class RuptureGenerationTask(ToshiClientBase):

    def __init__(self, toshi_api_url, s3_url, auth_token, with_schema_validation=True, headers=None ):
        super(RuptureGenerationTask, self).__init__(toshi_api_url, auth_token, with_schema_validation, headers)
        self.file_api = ToshiFile(toshi_api_url, s3_url, auth_token, with_schema_validation, headers)
        self.task_file_api = ToshiTaskFile(toshi_api_url, auth_token, with_schema_validation, headers)

    def upload_task_file(self, task_id, filepath):
        #upload file produced
        filepath = PurePath(filepath)
        file_id, post_url = self.file_api.create_file(filepath)
        self.file_api.upload_content(post_url, filepath)

        #link file in role
        task_file_id = self.task_file_api.create_task_file(task_id, file_id, 'WRITE')
        # print("Done", task_file_id)

    def get_example_create_variables(self):
        return {"started": "2019-10-01T12:00Z",
          "permutationStrategy": "DOWNDIP",
          "openshaCore": "A",
          "openshaCommons":"b",
          "openshaUcerf3":"C",
          "nshmNzOpensha":"D",
          "maxJumpDistance": 22.2,
          "maxSubSectionLength": 0.5,
          "maxCumulativeAzimuth": 501.0,
          "minSubSectionsPerParent": 2,
          }

    def get_example_complete_variables(self):
          return {"taskId": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=",
          "duration": 600,
          "result": "SUCCESS",
          "state": "DONE",
          "ruptureCount": 10,
          "subsectionCount": 100,
          "clusterConnectionCount": 100
           }

    def validate_variables(self, reference, values):
        valid_keys = reference.keys()
        if not values.keys() == valid_keys:
            diffs = set(valid_keys).difference(set(values.keys()))
            missing_keys = ", ".join(diffs)
            raise ValueError("complete_variables must contain keys: %s" % missing_keys)

    def complete_task(self, input_variables):
        qry = '''
            mutation complete_task (
              $taskId:ID!
              $duration: Float!
              $state:TaskState!
              $result:TaskResult!
              $subsectionCount:Int!
              $ruptureCount:Int!
              $clusterConnectionCount:Int!){
              updateRuptureGenerationTask(input:{
                taskId:$taskId
                duration:$duration
                result:$result
                state:$state
                metrics:{
                  ruptureCount:$ruptureCount
                  clusterConnectionCount:$clusterConnectionCount
                  subsectionCount:$subsectionCount
                }
              }) {
                taskResult {
                  id
                }
              }
            }

        '''
        self.validate_variables(self.get_example_complete_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['updateRuptureGenerationTask']['taskResult']['id']

    def create_task(self, input_variables):
        qry = '''
            mutation create_task ($started:DateTime!,
              $openshaCore:String!,
              $openshaCommons:String!,
              $openshaUcerf3:String!,
              $nshmNzOpensha: String!,
              $maxJumpDistance: Float!,
              $maxSubSectionLength: Float!,
              $maxCumulativeAzimuth: Float!,
              $minSubSectionsPerParent: Int!
              $permutationStrategy: RupturePermutationStrategy!
              ) {
              createRuptureGenerationTask (
                input: {
                  started: $started
                  state:STARTED
                  result:UNDEFINED

                  gitRefs: {
                    openshaCore: $openshaCore
                    openshaCommons: $openshaCommons
                    openshaUcerf3: $openshaUcerf3
                    nshmNzOpensha: $nshmNzOpensha
                  }
                  arguments: {
                    maxJumpDistance: $maxJumpDistance
                    maxSubSectionLength: $maxSubSectionLength
                    maxCumulativeAzimuth: $maxCumulativeAzimuth
                    minSubSectionsPerParent: $minSubSectionsPerParent
                    permutationStrategy: $permutationStrategy
                  }
                })
                {
                  taskResult {
                    id
                    }
                }
            }
        '''
        self.validate_variables(self.get_example_create_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['createRuptureGenerationTask']['taskResult']['id']
