from .toshi_client_base import ToshiClientBase

class ToshiTaskFile(ToshiClientBase):

    def __init__(self, url, auth_token, with_schema_validation=True, headers=None ):
        super(ToshiTaskFile, self).__init__(url, auth_token, with_schema_validation, headers)

    def create_task_file(self, task_id, file_id, task_role):
        qry = '''
        mutation create_task_file(
            $task_id:ID!
            $file_id:ID!
            $task_role:TaskFileRole!) {
              createTaskFile(
                fileId:$file_id
                taskId:$task_id
                taskRole:$task_role
              )
            {
              taskFile { id }
            }
        }'''

        variables = dict(task_id=task_id, file_id=file_id, task_role=task_role)
        executed = self.run_query(qry, variables)
        return executed['createTaskFile']['taskFile']['id']
