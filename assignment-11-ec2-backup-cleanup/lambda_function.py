import os
from datetime import datetime, timedelta, timezone

import boto3

s3 = boto3.client('s3')
ssm = boto3.client('ssm')

BUCKET_NAME = os.environ.get('BUCKET_NAME')
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))


def delete_old_backups(bucket_name, prefix, cutoff):
  deleted_keys = []
  paginator = s3.get_paginator('list_objects_v2')

  for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
    for obj in page.get('Contents', []):
      if obj['LastModified'] < cutoff:
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        deleted_keys.append(obj['Key'])
        print(f'Deleted old backup: {obj["Key"]}')

  return deleted_keys


def lambda_handler(event, context):
  instance_id = event.get('instance_id') or os.environ.get('INSTANCE_ID')
  bucket_name = event.get('bucket_name') or BUCKET_NAME
  paths = event.get('paths', '/var/log')
  prefix = event.get('prefix', 'backups/')

  if not instance_id or not bucket_name:
    return {
      'statusCode': 400,
      'body': {'error': 'instance_id and bucket_name are required'},
    }

  timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
  backup_key = f'{prefix}{instance_id}/{timestamp}.zip'
  command = (
    f'zip -r /tmp/backup.zip {paths} && '
    f'aws s3 cp /tmp/backup.zip s3://{bucket_name}/{backup_key}'
  )

  response = ssm.send_command(
    InstanceIds=[instance_id],
    DocumentName='AWS-RunShellScript',
    Parameters={'commands': [command]},
  )
  command_id = response['Command']['CommandId']
  print(f'Started backup command {command_id} for {instance_id}')

  cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
  deleted_keys = delete_old_backups(bucket_name, prefix, cutoff)

  return {
    'statusCode': 200,
    'body': {
      'instance_id': instance_id,
      'command_id': command_id,
      'backup_key': backup_key,
      'deleted_backups': deleted_keys,
    },
  }
