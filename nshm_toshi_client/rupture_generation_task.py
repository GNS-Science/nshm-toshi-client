import base64
import json
from datetime import datetime as dt
from datetime import timezone
from hashlib import md5
from os import PathLike
from pathlib import PurePath
from typing import Optional

from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_task_file import ToshiTaskFile

from .toshi_client_base import ToshiClientBase, kvl_to_graphql


class RuptureGenerationTask(ToshiClientBase):
    def __init__(self, toshi_api_url, s3_url, auth_token, with_schema_validation=True, headers=None):
        super(RuptureGenerationTask, self).__init__(toshi_api_url, auth_token, with_schema_validation, headers)
        self.file_api = ToshiFile(toshi_api_url, s3_url, auth_token, with_schema_validation, headers)
        self.task_file_api = ToshiTaskFile(toshi_api_url, auth_token, with_schema_validation, headers)

    def upload_rupture_set(
        self,
        task_id: str,
        filepath: str | PathLike,
        fault_models: list[str],
        arguments: Optional[dict] = None,
        metrics: Optional[dict] = None,
    ) -> str:
        """Create an inversion solution object and, upload the file and link it to the task.

        Args:
            task_id: the RuptureGenerationTask id
            filepath: path to the file to upload
            fault_models: list of fault models used to generate the rupture set
            arguments: arguments used to generate the rupture set
            metrics: metrics to attach to the rupture set

        Returns:
            the created rupture set id
        """
        filepath = PurePath(filepath)
        file_id, post_url, post_data = self._create_rupture_set(filepath, task_id, fault_models, arguments, metrics)
        self.file_api.upload_content_v2(post_url, post_data, filepath)
        self.task_file_api.create_task_file(task_id, file_id, 'WRITE')
        return file_id

    def _create_rupture_set(
        self,
        filepath: PurePath,
        task_id: str,
        fault_models: list[str],
        arguments: Optional[dict] = None,
        metrics: Optional[dict] = None,
    ) -> tuple[str, str, str]:
        qry = '''
            mutation (
                $md5_digest: String!,
                $file_name: String!,
                $file_size: BigInt!,
                $produced_by: ID!
                $arguments: [KeyValuePairInput],
                $metrics: [KeyValuePairInput],
                $created: DateTime!
                $fault_models: [String]!
            ) {
              create_rupture_set(input: {
                md5_digest: $md5_digest
                file_name: $file_name
                file_size: $file_size
                produced_by: $produced_by
                created: $created
                fault_models: $fault_models

                ##METRICS##

                ##ARGUMENTS##

                  }
              ) {
              rupture_set { id, post_url_v2, post_data_v2 }
              }
            }
        '''
        if arguments:
            qry = qry.replace("##ARGUMENTS##", kvl_to_graphql('arguments', arguments))
        if metrics:
            qry = qry.replace("##METRICS##", kvl_to_graphql('metrics', metrics))

        filedata = open(filepath, 'rb')
        digest = base64.b64encode(md5(filedata.read()).digest()).decode()

        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.close()

        created = dt.now(timezone.utc).isoformat() + 'Z'
        variables = dict(
            md5_digest=digest,
            file_name=filepath.parts[-1],
            file_size=size,
            produced_by=task_id,
            created=created,
            fault_models=fault_models,
        )

        executed = self.run_query(qry, variables)
        rupture_set_id = executed['create_rupture_set']['rupture_set']['id']
        post_url = json.loads(executed['create_rupture_set']['rupture_set']['post_url_v2'])
        post_data = json.loads(executed['create_rupture_set']['rupture_set']['post_data_v2'])

        return (rupture_set_id, post_url, post_data)

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
        return {
            "created": "2019-10-01T12:00Z",
            "task_type": "SOME_TASK_TYPE",
            "model_type": "SOME_MODEL_TYPE",
        }

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
            mutation create_task ($created: DateTime!, $task_type:TaskSubType!, $model_type:ModelType!) {
              create_rupture_generation_task (
                input: {
                  created: $created
                  task_type: $task_type
                  model_type: $model_type
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
