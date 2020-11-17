# from gql import gql
from hashlib import md5
import json
import base64
import requests
from pathlib import PurePath

from .toshi_client_base import ToshiClientBase
from nshm_toshi_client.toshi_file import ToshiFile
# from nshm_toshi_client.toshi_task_file import ToshiTaskFile
#from .toshi_file import ToshiFile

class StrongMotionStation(ToshiClientBase):

    def __init__(self, toshi_api_url, s3_url, auth_token, with_schema_validation=True, headers=None ):
        super(StrongMotionStation, self).__init__(toshi_api_url, auth_token, with_schema_validation, headers)
        self.file_api = ToshiFile(toshi_api_url, s3_url, auth_token, with_schema_validation, headers)
        # self.task_file_api = ToshiTaskFile(toshi_api_url, auth_token, with_schema_validation, headers)

    def upload_file(self, filepath):
        filepath = PurePath(filepath)
        file_id, post_url = self.file_api.create_file(filepath)
        self.file_api.upload_content(post_url, filepath)
        return file_id

    def link_task_file(self, task_id, file_id, task_role):
        return self.task_file_api.create_task_file(task_id, file_id, task_role)

    def upload_task_file(self, task_id, filepath, task_role):
        filepath = PurePath(filepath)
        file_id = self.upload_file(filepath)
        #link file to task in role
        return self.link_task_file(task_id, file_id, task_role)

    def get_example_create_variables(self):
        return {
            "created": "2019-10-01T12:00Z",
            "site_code": "BBBB",
            "site_class": "E",
            "Vs30_mean": [1.24,]
          }

    def get_example_complete_variables(self):
          return {"id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=",
           }

    def validate_variables(self, reference, values):
        valid_keys = reference.keys()
        if not values.keys() == valid_keys:
            diffs = set(valid_keys).difference(set(values.keys()))
            missing_keys = ", ".join(diffs)
            raise ValueError(" mutation variables must contain keys: %s" % missing_keys)

    # def complete_task(self, input_variables):
    #     qry = '''
    #         mutation complete_task (
    #           $taskId:ID!
    #           $duration: Float!
    #           $state:TaskState!
    #           $result:TaskResult!
    #           $subsectionCount:Int!
    #           $ruptureCount:Int!
    #           $clusterConnectionCount:Int!){
    #           updateStrongMotionStation(input:{
    #             taskId:$taskId
    #             duration:$duration
    #             result:$result
    #             state:$state
    #             metrics:{
    #               ruptureCount:$ruptureCount
    #               clusterConnectionCount:$clusterConnectionCount
    #               subsectionCount:$subsectionCount
    #             }
    #           }) {
    #             taskResult {
    #               id
    #             }
    #           }
    #         }

    #     '''
    #     self.validate_variables(self.get_example_complete_variables(), input_variables)
    #     executed = self.run_query(qry, input_variables)
    #     return executed['updateStrongMotionStation']['taskResult']['id']

    def create(self, input_variables):
        qry = '''
            mutation create_strong_motion_station (
                $created: DateTime!,
                $site_code: String!,
                $site_class: SmsSiteClass!,
                $Vs30_mean: [Float!],
              ) {
              create_strong_motion_station (
                input: {
                    created: $created
                    site_code: $site_code
                    site_class: $site_class
                    Vs30_mean: $Vs30_mean
                })
                {
                  strong_motion_station  {
                    id
                    }
                }
            }
        '''
        self.validate_variables(self.get_example_create_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['create_strong_motion_station']['strong_motion_station']['id']

    def list(self):
        qry = '''
        query search_sms {
          search(
            search_term: "clazz_name:StrongMotionStation&size=200&sort=created:asc"
            )
            {
            search_result {
              edges {
                node {
                  ... on StrongMotionStation {
                    id
                    site_code
                    created
                    site_class
                    site_class_basis
                    Vs30_mean
                    bedrock_encountered
                  }
                }
              }
            }
          }
        }
        '''
        executed = self.run_query(qry)
        # print(executed)
        edges = executed['search']['search_result']['edges']
        return [e['node'] for e in edges]
