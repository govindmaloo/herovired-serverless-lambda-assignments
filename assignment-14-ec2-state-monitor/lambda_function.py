import os

import boto3

sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')


def lambda_handler(event, context):
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN
  if not sns_topic_arn:
    return {'statusCode': 400, 'body': {'error': 'SNS_TOPIC_ARN is required'}}

  detail = event.get('detail', {})
  instance_id = detail.get('instance-id') or event.get('instance_id')
  state = detail.get('state') or event.get('state')

  if not instance_id or not state:
    return {'statusCode': 400, 'body': {'error': 'EC2 state change event is required'}}

  message = f'EC2 instance {instance_id} changed state to {state}'
  sns.publish(
    TopicArn=sns_topic_arn,
    Subject='EC2 Instance State Change',
    Message=message,
  )
  print(message)

  return {
    'statusCode': 200,
    'body': {
      'instance_id': instance_id,
      'state': state,
      'message': message,
    },
  }
