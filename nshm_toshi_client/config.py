import os

API_URL = os.getenv('NZSHM22_TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
S3_URL = os.getenv('NZSHM22_TOSHI_S3_URL', "http://localhost:4569")
API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")

# M2M JWT auth (Cognito client credentials grant)
COGNITO_DOMAIN = os.getenv('NZSHM22_TOSHI_COGNITO_DOMAIN', '')

# Interactive/scientist auth (Cognito user pool)
COGNITO_SCIENTIST_CLIENT_ID = os.getenv('NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID', '')
COGNITO_REGION = os.getenv('NZSHM22_TOSHI_COGNITO_REGION', 'ap-southeast-2')
COGNITO_USER_POOL_ID = os.getenv('NZSHM22_TOSHI_COGNITO_USER_POOL_ID', '')
