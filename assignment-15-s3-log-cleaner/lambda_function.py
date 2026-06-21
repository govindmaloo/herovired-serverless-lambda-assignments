import os
from datetime import datetime, timedelta, timezone

import boto3

s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('BUCKET_NAME')
LOG_PREFIX = os.environ.get('LOG_PREFIX', '')
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '90'))


def lambda_handler(event, context):
  bucket_name = event.get('bucket_name') or BUCKET_NAME
  prefix = event.get('prefix', LOG_PREFIX)
  retention_days = int(event.get('days', RETENTION_DAYS))

  if not bucket_name:
    return {'statusCode': 400, 'body': {'error': 'bucket_name is required'}}

  cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
  deleted_objects = []

  paginator = s3.get_paginator('list_objects_v2')
  for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
    for obj in page.get('Contents', []):
      if obj['LastModified'] < cutoff:
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        deleted_objects.append(obj['Key'])
        print(f'Deleted log: {obj["Key"]}')

  print(f'Deleted {len(deleted_objects)} logs older than {retention_days} days')

  return {
    'statusCode': 200,
    'body': {
      'bucket': bucket_name,
      'deleted_objects': deleted_objects,
    },
  }
