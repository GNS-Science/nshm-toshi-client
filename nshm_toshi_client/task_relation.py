from .toshi_client_base import ToshiClientBase


class TaskRelation(ToshiClientBase):
    def __init__(self, url, auth_token, with_schema_validation=True, headers=None):
        super(TaskRelation, self).__init__(url, auth_token, with_schema_validation, headers)

    def create_task_relation(self, parent_id, child_id):
        qry = '''
        mutation (
            $parent_id:ID!
            $child_id:ID!
        	) {
              create_task_relation(
                child_id:$child_id
                parent_id:$parent_id
              )
            {
              ok
            }
        }'''
        variables = dict(parent_id=parent_id, child_id=child_id)
        executed = self.run_query(qry, variables)
        return executed['create_task_relation']['ok']
