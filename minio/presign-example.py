import boto3
from botocore.client import Config
from botocore import UNSIGNED
from botocore.config import Config as BotoConfig
import requests
import urllib3

#pip install boto3 requests

#make sure minio port 9000 is forwarded to localhost.
# to test cluster site replication, debug this script and break after getting the url. Then forward port 9000 of the replicated cluster and continue the script. This will have requested the presigned URL from cluster1 and used it on cluster2

# Suppress only the single InsecureRequestWarning from urllib3 needed for this specific request
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
minio_url = 'https://localhost:9000'  # Replace with your MinIO server URL
access_key = 'minio'  # Replace with your MinIO access key
secret_key = 'password'  # Replace with your MinIO secret key
bucket_name = 'test-bucket1'   # Replace with your bucket name
object_name = 'README.md'   # Replace with your object name
file_path = 'README.md'  # Replace with the path to your file

# Create a session
session = boto3.session.Session()

# Create a S3 client with unsigned config to avoid SSL certificate validation
s3_client = session.client(
    's3',
    endpoint_url=minio_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=BotoConfig(signature_version='s3v4', retries={'max_attempts': 0}),
    region_name='us-east-1'
)

# Generate a presigned URL for the PUT operation
url = s3_client.generate_presigned_url(
    ClientMethod='put_object',
    Params={'Bucket': bucket_name, 'Key': object_name},
    ExpiresIn=3600  # URL expiration time in seconds
)

print(f"Presigned URL: {url}")

# Upload the file using the presigned URL without certificate validation
with open(file_path, 'rb') as file_data:
    response = requests.put(url, data=file_data, verify=False)

# Check the response
if response.status_code == 200:
    print("File uploaded successfully.")
    print(f"Response: {response.text}")
else:
    print(f"Failed to upload file. Status code: {response.status_code}")
    print(f"Response: {response.text}")
