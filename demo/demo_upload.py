from hashlib import sha256

from gql import gql, Client, AIOHTTPTransport
from gql.transport.requests import RequestsHTTPTransport

sample_transport=RequestsHTTPTransport(
    url='http://127.0.0.1:5000/graphql',
    verify=False,
    retries=3,
)

#transport = AIOHTTPTransport(url='http://127.0.0.1:5000/graphql')
transport = AIOHTTPTransport(url='https://qsz8j27tw6.execute-api.ap-southeast-2.amazonaws.com/test/graphql')

class DataFileClient():

    def __init__(self):
        #set client here
        self.client = Client(
	    	transport=transport,
		    fetch_schema_from_transport=True
		)

    def upload(self, filename):
        qry = gql('''
            mutation ($file: Upload!, $digest: String!, $file_name: String!, $file_size: BigInt!) {
              createFile(
                  fileIn: $file
                  hexDigest: $digest
                  fileName: $file_name
                  fileSize: $file_size
              ) {
                  ok
                  fileResult { id, fileName, fileSize, hexDigest }
              }
            }''')
        filedata = open(filename, 'rb')
        try:
            digest = sha256(filedata.read()).hexdigest()
        except UnicodeDecodeError:
            digest = sha256(filedata.read().decode()).hexdigest()
        filedata.seek(0) #important!
        size = len(filedata.read())
        filedata.seek(0) #important!
        variables = dict(file=filedata, digest=digest, file_name=filename, file_size=size)
        executed = self.client.execute(qry, variable_values=variables, upload_files=True)
        print(executed)


if __name__ == "__main__":
    myapi = DataFileClient()
    #myapi.upload("requirements.txt")
    myapi.upload("../opensha/nshm-nz-opensha/data/ruptureSets/CFM_SANSTVZ_5.1km_downdip.zip")
