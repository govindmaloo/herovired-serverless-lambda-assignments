import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')


def lambda_handler(event, context):
  unencrypted_buckets = []

  for bucket in s3.list_buckets()['Buckets']:
    bucket_name = bucket['Name']
    try:
      s3.get_bucket_encryption(Bucket=bucket_name)
    except ClientError as error:
      code = error.response['Error']['Code']
      if code in (
        'ServerSideEncryptionConfigurationNotFoundError',
        'NoSuchBucketEncryptionConfiguration',
      ):
        print(f'Unencrypted bucket: {bucket_name}')
        unencrypted_buckets.append(bucket_name)
      else:
        print(f'Error checking {bucket_name}: {error}')

  return {
    'statusCode': 200,
    'body': {
      'unencrypted_buckets': unencrypted_buckets,
    },
  }
