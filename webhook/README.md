# get a key

openssl rand -hex 16

# install python libs

pip install Flask confluent-kafka six


# run app and test

python .\webhook.py

curl -X POST http://F1NBK6312:5000/webhook -H "Authorization: 9f6d4e30a7d3e4a9b10c8d34d5f3a234" -H "Content-Type: application/json" -d '{"event":"test"}'

# Hooking into Weka makes it quite chatty

{'auditVersion': '1.weka', 'wekaInfo': {'version': '4.2.8.66', 'release': '4.2.8.66', 'clusterGUID': 'd5adf63c-054e-48cf-9f58-7e076d6fe222', 
'clusterName': 'mercedes-amg-testdev', 'serverIP': '172.26.190.105', 'serverName': 'devlbnode2-1.dev.weka.barf1.com'}, 'deploymentid': 'b143574a-767c-4069-a4a5-5d7262e0ea40', 'time': '2024-05-28T11:26:44.018172514Z', 'api': {'name': 'ListBuckets', 'status': 'OK', 'statusCode': 200, 'timeToFirstByte': '485423ns', 'timeToResponse': '518594ns'}, 'remotehost': '127.0.0.1', 'requestID': '17D3A37491E66B97', 'userAgent': 'Boto3/1.34.29 md/Botocore#1.34.29 ua/2.0 os/linux#5.15.0-25-generic md/arch#x86_64 lang/python#3.8.10 md/pyimpl#CPython cfg/retry-mode#legacy Botocore/1.34.29', 'requestHeader': {'Accept-Encoding': 'identity', 'Amz-Sdk-Invocation-Id': 'a6cc99dd-21f1-4c5d-a417-c0d16b441287', 'Amz-Sdk-Request': 'attempt=1', 'Authorization': 'AWS4-HMAC-SHA256 Credential=cSx5l3TYycket7rJHfqZFRFz9GYHP4HBQUB03KUOeKO5SlonITtF2dqvndauBXSRl1I00AOMx4nWttD8TslwDjd4E2NxJ9uR4QBps60AFSOfE6ms5s9NecBLDByxRTlz/20240528/ignored-by-minio/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=1b4f33b38e89644fb04562a2cde124f208eb4f5d4b0254fbded1193b16448bc2', 'User-Agent': 'Boto3/1.34.29 md/Botocore#1.34.29 ua/2.0 os/linux#5.15.0-25-generic md/arch#x86_64 lang/python#3.8.10 md/pyimpl#CPython cfg/retry-mode#legacy Botocore/1.34.29', 'X-Amz-Content-Sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'X-Amz-Date': '20240528T112644Z'}, 'responseHeader': {'Accept-Ranges': 'bytes', 'Content-Length': '546', 'Content-Security-Policy': 'block-all-mixed-content', 'Content-Type': 'application/xml', 'ETag': '', 'Server': 'MinIO', 'Vary': 'Origin', 'X-Amz-Request-Id': '17D3A37491E66B97', 'X-Xss-Protection': '1; mode=block'}}

Eg lots of `ListBuckets` events