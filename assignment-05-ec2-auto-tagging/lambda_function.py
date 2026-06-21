import os
from datetime import datetime, timezone

import boto3

ec2 = boto3.client('ec2')

CUSTOM_TAG_KEY = os.environ.get('CUSTOM_TAG_KEY', 'Environment')
CUSTOM_TAG_VALUE = os.environ.get('CUSTOM_TAG_VALUE', 'Dev')


def get_instance_id(event):
  detail = event.get('detail', {})
  if detail.get('instance-id'):
    return detail['instance-id']
  return event.get('instance_id')


def lambda_handler(event, context):
  instance_id = get_instance_id(event)
  if not instance_id:
    return {'statusCode': 400, 'body': {'error': 'instance_id is required'}}

  launch_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
  ec2.create_tags(
    Resources=[instance_id],
    Tags=[
      {'Key': 'LaunchDate', 'Value': launch_date},
      {'Key': CUSTOM_TAG_KEY, 'Value': CUSTOM_TAG_VALUE},
    ],
  )

  print(f'Tagged instance {instance_id} with LaunchDate={launch_date}')

  return {
    'statusCode': 200,
    'body': {
      'tagged_instance_id': instance_id,
      'launch_date': launch_date,
    },
  }
