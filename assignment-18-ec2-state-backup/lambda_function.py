import json
import os

import boto3

ec2 = boto3.client('ec2')
s3 = boto3.client('s3')

BUCKET_NAME = os.environ.get('BUCKET_NAME')


def lambda_handler(event, context):
  bucket_name = event.get('bucket_name') or BUCKET_NAME
  detail = event.get('detail', {})
  instance_id = detail.get('instance-id') or event.get('instance_id')
  state = detail.get('state')

  if not bucket_name:
    return {'statusCode': 400, 'body': {'error': 'bucket_name is required'}}
  if not instance_id:
    return {'statusCode': 400, 'body': {'error': 'instance_id is required'}}

  reservations = ec2.describe_instances(InstanceIds=[instance_id])['Reservations']
  if not reservations:
    return {'statusCode': 404, 'body': {'error': f'Instance {instance_id} not found'}}

  instance = reservations[0]['Instances'][0]
  saved_snapshots = []

  for mapping in instance.get('BlockDeviceMappings', []):
    if 'Ebs' not in mapping:
      continue

    volume_id = mapping['Ebs']['VolumeId']
    snapshot = ec2.create_snapshot(
      VolumeId=volume_id,
      Description=f'Pre-shutdown backup for {instance_id}',
    )
    snapshot_id = snapshot['SnapshotId']
    saved_snapshots.append(snapshot_id)

    state_payload = {
      'instance_id': instance_id,
      'state': state,
      'volume_id': volume_id,
      'snapshot_id': snapshot_id,
      'instance_type': instance.get('InstanceType'),
      'tags': instance.get('Tags', []),
    }
    key = f'{instance_id}/{snapshot_id}.json'
    s3.put_object(
      Bucket=bucket_name,
      Key=key,
      Body=json.dumps(state_payload, default=str),
      ContentType='application/json',
    )
    print(f'Saved state for {instance_id} to s3://{bucket_name}/{key}')

  return {
    'statusCode': 200,
    'body': {
      'instance_id': instance_id,
      'state': state,
      'snapshots': saved_snapshots,
    },
  }
