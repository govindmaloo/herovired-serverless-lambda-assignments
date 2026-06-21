import json
import os

import boto3

sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')


def lambda_handler(event, context):
  if not SNS_TOPIC_ARN:
    return {'statusCode': 400, 'body': {'error': 'SNS_TOPIC_ARN is required'}}

  notifications = []

  for record in event.get('Records', []):
    event_name = record.get('eventName')
    if event_name not in ('INSERT', 'MODIFY', 'REMOVE'):
      continue

    keys = record.get('dynamodb', {}).get('Keys', {})
    new_image = record.get('dynamodb', {}).get('NewImage', {})
    old_image = record.get('dynamodb', {}).get('OldImage', {})

    message = {
      'event': event_name,
      'keys': keys,
      'new_image': new_image,
      'old_image': old_image,
    }
    message_text = json.dumps(message, default=str)

    sns.publish(
      TopicArn=SNS_TOPIC_ARN,
      Subject=f'DynamoDB item {event_name}',
      Message=message_text,
    )
    print(f'Sent alert for DynamoDB {event_name}: {message_text}')
    notifications.append(message)

  return {
    'statusCode': 200,
    'body': {
      'notifications_sent': len(notifications),
      'changes': notifications,
    },
  }
