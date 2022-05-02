# from gql import gql
import base64
import json
from hashlib import md5
from pathlib import PurePath

import requests

from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_task_file import ToshiTaskFile

from .toshi_client_base import ToshiClientBase, kvl_to_graphql


class RuptureGenerationTask(ToshiClientBase):
    def __init__(self, toshi_api_url, s3_url, auth_token, with_schema_validation=True, headers=None):
        super(RuptureGenerationTask, self).__init__(toshi_api_url, auth_token, with_schema_validation, headers)
        self.file_api = ToshiFile(toshi_api_url, s3_url, auth_token, with_schema_validation, headers)
        self.task_file_api = ToshiTaskFile(toshi_api_url, auth_token, with_schema_validation, headers)

    def upload_file(self, filepath, meta=None):
        filepath = PurePath(filepath)
        file_id, post_url = self.file_api.create_file(filepath, meta)
        self.file_api.upload_content(post_url, filepath)
        return file_id

    def link_task_file(self, task_id, file_id, task_role):
        return self.task_file_api.create_task_file(task_id, file_id, task_role)

    def upload_task_file(self, task_id, filepath, task_role, meta=None):
        filepath = PurePath(filepath)
        file_id = self.upload_file(filepath, meta)
        # link file to task in role
        return self.link_task_file(task_id, file_id, task_role)

    def get_example_create_variables(self):
        return {"created": "2019-10-01T12:00Z"}

    def get_example_complete_variables(self):
        return {"task_id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjA=", "duration": 600, "result": "SUCCESS", "state": "DONE"}

    def validate_variables(self, reference, values):
        valid_keys = reference.keys()
        if not values.keys() == valid_keys:
            diffs = set(valid_keys).difference(set(values.keys()))
            missing_keys = ", ".join(diffs)
            raise ValueError("complete_variables must contain keys: %s" % missing_keys)

    def complete_task(self, input_variables, metrics=None):
        qry = '''
            mutation complete_task (
              $task_id:ID!
              $duration: Float!
              $state:EventState!
              $result:EventResult!
            ){
              update_rupture_generation_task(input:{
                task_id:$task_id
                duration:$duration
                result:$result
                state:$state

                ##METRICS##

              }) {
                task_result {
                  id
                  metrics {k v}
                }
              }
            }

        '''

        if metrics:
            qry = qry.replace("##METRICS##", kvl_to_graphql('metrics', metrics))

        print(qry)

        self.validate_variables(self.get_example_complete_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['update_rupture_generation_task']['task_result']['id']

    def create_task(self, input_variables, arguments=None, environment=None):
        qry = '''
            mutation create_task ($created:DateTime!) {
              create_rupture_generation_task (
                input: {
                  created: $created
                  state:STARTED
                  result:UNDEFINED

                  ##ARGUMENTS##

                  ##ENVIRONMENT##
                })
                {
                  task_result {
                    id
                    }
                }
            }
        '''

        if arguments:
            qry = qry.replace("##ARGUMENTS##", kvl_to_graphql('arguments', arguments))
        if environment:
            qry = qry.replace("##ENVIRONMENT##", kvl_to_graphql('environment', environment))

        print(qry)
        self.validate_variables(self.get_example_create_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['create_rupture_generation_task']['task_result']['id']
