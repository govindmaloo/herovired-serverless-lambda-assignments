import os
from datetime import datetime, timedelta, timezone

import boto3

s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('BUCKET_NAME')
ARCHIVE_DAYS = int(os.environ.get('ARCHIVE_DAYS', '180'))


def lambda_handler(event, context):
  bucket_name = event.get('bucket_name') or BUCKET_NAME
  if not bucket_name:
    return {'statusCode': 400, 'body': {'error': 'bucket_name is required'}}

  cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVE_DAYS)
  archived_keys = []

  paginator = s3.get_paginator('list_objects_v2')
  for page in paginator.paginate(Bucket=bucket_name):
    for obj in page.get('Contents', []):
      if obj['LastModified'] >= cutoff:
        continue

      key = obj['Key']
      s3.copy_object(
        Bucket=bucket_name,
        Key=key,
        CopySource={'Bucket': bucket_name, 'Key': key},
        StorageClass='GLACIER',
      )
      archived_keys.append(key)
      print(f'Archived to Glacier: {key}')

  return {
    'statusCode': 200,
    'body': {
      'bucket': bucket_name,
      'archived_objects': archived_keys,
    },
  }
