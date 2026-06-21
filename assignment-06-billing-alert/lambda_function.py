import os
from datetime import datetime, timedelta, timezone

import boto3

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
BILLING_THRESHOLD = float(os.environ.get('BILLING_THRESHOLD', '50'))


def lambda_handler(event, context):
  if not SNS_TOPIC_ARN:
    return {'statusCode': 400, 'body': {'error': 'SNS_TOPIC_ARN is required'}}

  end_time = datetime.now(timezone.utc)
  start_time = end_time - timedelta(days=1)

  response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Billing',
    MetricName='EstimatedCharges',
    Dimensions=[{'Name': 'Currency', 'Value': 'USD'}],
    StartTime=start_time,
    EndTime=end_time,
    Period=86400,
    Statistics=['Maximum'],
  )

  datapoints = response.get('Datapoints', [])
  if not datapoints:
    print('No billing datapoints found')
    return {'statusCode': 200, 'body': {'message': 'No billing data available'}}

  billing_amount = max(point['Maximum'] for point in datapoints)
  print(f'Current estimated charges: ${billing_amount:.2f}')

  if billing_amount > BILLING_THRESHOLD:
    message = (
      f'AWS billing alert: estimated charges ${billing_amount:.2f} '
      f'exceed threshold ${BILLING_THRESHOLD:.2f}'
    )
    sns.publish(
      TopicArn=SNS_TOPIC_ARN,
      Subject='AWS Billing Threshold Exceeded',
      Message=message,
    )
    print(message)
    return {
      'statusCode': 200,
      'body': {'alert_sent': True, 'billing_amount': billing_amount},
    }

  print(f'Billing ${billing_amount:.2f} is within threshold')
  return {
    'statusCode': 200,
    'body': {'alert_sent': False, 'billing_amount': billing_amount},
  }
