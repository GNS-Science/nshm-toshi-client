from .toshi_client_base import ToshiClientBase

class ToshiTaskFile(ToshiClientBase):

    def __init__(self, url, auth_token, with_schema_validation=True, headers=None ):
        super(ToshiTaskFile, self).__init__(url, auth_token, with_schema_validation, headers)

    def create_task_file(self, task_id, file_id, role):
        qry = '''
        mutation create_file_link(
            $task_id:ID!
            $file_id:ID!
            $role:FileRole!) {
              create_file_link(
                file_id:$file_id
                thing_id:$task_id
                role:$role
              )
            {
              file_link { id }
            }
        }'''
        variables = dict(task_id=task_id, file_id=file_id, role=task_role)
        executed = self.run_query(qry, variables)
        return executed['create_file_link']['file_link']['id']

