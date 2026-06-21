import os
from datetime import datetime, timedelta, timezone

import boto3

ec2 = boto3.client('ec2')

RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', '30'))


def lambda_handler(event, context):
  volume_id = event.get('volume_id') or os.environ.get('VOLUME_ID')
  if not volume_id:
    return {'statusCode': 400, 'body': {'error': 'volume_id is required'}}

  snapshot = ec2.create_snapshot(
    VolumeId=volume_id,
    Description=f'Automated snapshot of {volume_id}',
  )
  created_snapshot_id = snapshot['SnapshotId']
  print(f'Created snapshot: {created_snapshot_id}')

  cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
  deleted_snapshots = []

  paginator = ec2.get_paginator('describe_snapshots')
  for page in paginator.paginate(OwnerIds=['self']):
    for item in page['Snapshots']:
      if item['StartTime'] < cutoff:
        ec2.delete_snapshot(SnapshotId=item['SnapshotId'])
        deleted_snapshots.append(item['SnapshotId'])
        print(f'Deleted snapshot: {item["SnapshotId"]}')

  return {
    'statusCode': 200,
    'body': {
      'created_snapshot_id': created_snapshot_id,
      'deleted_snapshots': deleted_snapshots,
    },
  }
