# from gql import gql
from hashlib import md5
import json
import base64
import requests
from pathlib import PurePath

from .toshi_client_base import ToshiClientBase
from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_task_file import ToshiTaskFile
from .toshi_client_base import ToshiClientBase, kvl_to_graphql

class GeneralTask(ToshiClientBase):

    def __init__(self, toshi_api_url, s3_url, auth_token, with_schema_validation=True, headers=None ):
        super(GeneralTask, self).__init__(toshi_api_url, auth_token, with_schema_validation, headers)
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

    def create_task(self, input_variables, arguments=None, environment=None):
        '''
        created: DateTime
        When the taskrecord was created
        updated: DateTime
        When task was updated
        agent_name: String
        The name of the person or process responsible for the task
        title: String
        A title always helps
        description: String
        Some description of the task, potentially Markdown
        '''

        qry = '''
            mutation ($created:DateTime!, $agent_name:String!, $title:String!, $description:String!) {
              create_general_task (
                input: {
                  created: $created
                  agent_name: $agent_name
                  title: $title
                  description: $description
                })
                {
                  task_result {
                    id
                    }
                }
            }
        '''
        print(qry)
        self.validate_variables(self.get_example_create_variables(), input_variables)
        executed = self.run_query(qry, input_variables)
        return executed['create_general_task']['task_result']['id']

