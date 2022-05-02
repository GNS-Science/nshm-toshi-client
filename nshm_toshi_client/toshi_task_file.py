from .toshi_client_base import ToshiClientBase


class ToshiTaskFile(ToshiClientBase):
    def __init__(self, url, auth_token, with_schema_validation=True, headers=None):
        super(ToshiTaskFile, self).__init__(url, auth_token, with_schema_validation, headers)

    def create_task_file(self, task_id, file_id, role):
        qry = '''
        mutation create_file_relation(
            $thing_id:ID!
            $file_id:ID!
            $role:FileRole!) {
              create_file_relation(
                file_id:$file_id
                thing_id:$thing_id
                role:$role
              )
            {
              ok
            }
        }'''
        variables = dict(thing_id=task_id, file_id=file_id, role=role)
        executed = self.run_query(qry, variables)
        return executed['create_file_relation']['ok']
