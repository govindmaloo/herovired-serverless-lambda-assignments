import os
from datetime import datetime, timedelta, timezone

import boto3

s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('BUCKET_NAME')
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))


def lambda_handler(event, context):
  bucket_name = event.get('bucket_name') or BUCKET_NAME
  if not bucket_name:
    return {'statusCode': 400, 'body': {'error': 'bucket_name is required'}}

  cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
  deleted_keys = []
  batch = []

  paginator = s3.get_paginator('list_objects_v2')
  for page in paginator.paginate(Bucket=bucket_name):
    for obj in page.get('Contents', []):
      if obj['LastModified'] < cutoff:
        batch.append({'Key': obj['Key']})
        deleted_keys.append(obj['Key'])
        print(f'Deleting object: {obj["Key"]}')

        if len(batch) == 1000:
          s3.delete_objects(Bucket=bucket_name, Delete={'Objects': batch})
          batch = []

  if batch:
    s3.delete_objects(Bucket=bucket_name, Delete={'Objects': batch})

  print(f'Deleted {len(deleted_keys)} objects from {bucket_name}')

  return {
    'statusCode': 200,
    'body': {
      'bucket': bucket_name,
      'deleted_objects': deleted_keys,
    },
  }
