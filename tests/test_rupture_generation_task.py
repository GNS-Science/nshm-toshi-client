"""
Test RuptureGenerationTask
"""

import requests_mock

from nshm_toshi_client.rupture_generation_task import RuptureGenerationTask

API_URL = "http://fake_api/graphql"
S3_URL = "https://some-tosh-api.com/"


def test_create_rupture_generation_task():
    with requests_mock.Mocker() as mocker:

        query_server_answer = '''
            {"data":
                {"create_rupture_generation_task":
                    {"task_result": {"id": "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjEwMjA1Ng==" } }
                }
            }
        '''

        mocker.post(API_URL, text=query_server_answer)
        headers = {"x-api-key": "THE_API_KEY"}
        myapi = RuptureGenerationTask(API_URL, S3_URL, None, with_schema_validation=False, headers=headers)

        create_vars = {
            "created": "2019-10-01T12:00Z",
            "task_type": "SOME_TASK_TYPE",
            "model_type": "SOME_MODEL_TYPE",
        }
        task_id = myapi.create_task(create_vars)
        assert task_id == "UnVwdHVyZUdlbmVyYXRpb25UYXNrOjEwMjA1Ng=="
