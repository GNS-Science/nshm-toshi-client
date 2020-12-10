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
        return {"created": "2019-10-01T12:00Z",
          "permutation_strategy": "DOWNDIP",
          "opensha_core": "A",
          "opensha_commons":"b",
          "opensha_ucerf3":"C",
          "nshm_nz_opensha":"D",
          "max_jump_distance": 22.2,
          "max_sub_section_length": 0.5,
          "max_cumulative_azimuth": 501.0,
          "min_sub_sections_per_parent": 2,
          }

    def get_example_complete_variables(self):
          return {"task_id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=",
          "duration": 600,
          "result": "SUCCESS",
          "state": "DONE",
          "rupture_count": 10,
          "subsection_count": 100,
          "cluster_connection_count": 100
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
              $task_id:ID!
              $duration: Float!
              $state:TaskState!
              $result:TaskResult!
              $subsection_count:Int!
              $rupture_count:Int!
              $cluster_connection_count:Int!){
              update_rupture_generation_task(input:{
                task_id:$task_id
                duration:$duration
                result:$result
                state:$state
                metrics:{
                  rupture_count:$rupture_count
                  cluster_connection_count:$cluster_connection_count
                  subsection_count:$subsection_count
                }
              }) {
                task_result {
                  id
                }
              }
            }

        '''
        self.validate_variables(self.get_example_complete_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['update_rupture_generation_task']['task_result']['id']

    def create_task(self, input_variables):
        qry = '''
            mutation create_task ($created:DateTime!,
              $opensha_core:String!,
              $opensha_commons:String!,
              $opensha_ucerf3:String!,
              $nshm_nz_opensha: String!,
              $max_jump_distance: Float!,
              $max_sub_section_length: Float!,
              $max_cumulative_azimuth: Float!,
              $min_sub_sections_per_parent: Int!
              $permutation_strategy: RupturePermutationStrategy!
              ) {
              create_rupture_generation_task (
                input: {
                  created: $created
                  state:STARTED
                  result:UNDEFINED

                  git_refs: {
                    opensha_core: $opensha_core
                    opensha_commons: $opensha_commons
                    opensha_ucerf3: $opensha_ucerf3
                    nshm_nz_opensha: $nshm_nz_opensha
                  }
                  arguments: {
                    max_jump_distance: $max_jump_distance
                    max_sub_section_length: $max_sub_section_length
                    max_cumulative_azimuth: $max_cumulative_azimuth
                    min_sub_sections_per_parent: $min_sub_sections_per_parent
                    permutation_strategy: $permutation_strategy
                  }
                })
                {
                  task_result {
                    id
                    }
                }
            }
        '''
        self.validate_variables(self.get_example_create_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['create_rupture_generation_task']['task_result']['id']

